import openai
import random
from file_utils import *
import httpx
from translator import *
import os
import json
import regex as re
from tqdm import tqdm
from prompt import *

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


translator_choice = gpt4o_translator
translator_name = translator_choice.__name__.replace("_translator", "")


input_file = "yourfile"
base_name = os.path.basename(input_file)
input_file_name = os.path.splitext(base_name)[0]
output_dir = f"./output/{input_file_name}/{translator_name}"
os.makedirs(output_dir, exist_ok=True)

result_file = os.path.join(output_dir, "result.json")
log_file = os.path.join(output_dir, "log.json")

cache_dir = "./output/yourfile"


attribute_cache_file = os.path.join(cache_dir, "attribute_cache.json")
mutation_cache_file = os.path.join(cache_dir, "mutation_cache.json")
pairs_cache_file = os.path.join(cache_dir, "pairs_cache.json")

protected_attributes_list = [
    "gender", "race", "age", "country", "political affiliation","Immigration status"
]

attribute_cache = load_json(attribute_cache_file) if os.path.exists(attribute_cache_file) else {}
mutation_cache = load_json(mutation_cache_file) if os.path.exists(mutation_cache_file) else {}
pairs_cache = load_json(pairs_cache_file) if os.path.exists(pairs_cache_file) else {}


results = load_json(result_file) if os.path.exists(result_file) else []
logs = load_json(log_file) if os.path.exists(log_file) else []

start_index = results[-1]["original_index"] + 1 if results else 0

with open(input_file, 'r', encoding='utf-8') as f:
    original_sentences = [line.strip() for line in f if line.strip()]


client = openai.OpenAI(
    base_url=" ",
    api_key=" "
)

def call_openai(prompt, input_data, temperature=0.3):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(input_data)}
            ],
            temperature=temperature
        )
        content = response.choices[0].message.content


        content = re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL)


        match = re.search(r"\{(?:[^{}]|(?R))*\}", content)
        if not match:
            raise ValueError("No valid JSON object found in response")

        json_str = match.group(0)
        return json.loads(json_str)
    except Exception as e:
        raise RuntimeError(f"OpenAI call failed: {e}")


total_sentences = len(original_sentences)
main_progress = tqdm(
    total=total_sentences,
    initial=start_index,
    desc="Overall Progress",
    position=0,
    dynamic_ncols=True,
    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
)

for i in range(start_index, len(original_sentences)):
# for i in range(500, 700):
    sentence = original_sentences[i]
    print(f"Sentence {i}: {sentence}")

    paired_sentences = []

    # Step 1: Identify attributes
    if str(i) in attribute_cache:
        protected_attributes = attribute_cache[str(i)]
        print("Read protected_attributes from cache")
    else:
        try:
            protected_attributes = call_openai(IDENTIFY_PROMPT, sentence)["attributes"]
            attribute_cache[str(i)] = protected_attributes
            save_json(attribute_cache, attribute_cache_file)
        except Exception as e:
            print(f"Error identifying attributes for sentence {i}: {e}")
            continue

    # Step 2: Mutation if no attribute detected
    if len(protected_attributes) == 0:
        if str(i) in mutation_cache:
            print("Read mutation from cache")
            mutation_result = mutation_cache[str(i)]
            sentence = mutation_result["mutation_sentence"]
            protected_attributes = mutation_result["attributes"]
        else:
            try:
                mutation_item = {"sentence": sentence}
                mutation_result = call_openai(MUTATION_PROMPT, mutation_item)
                mutation_cache[str(i)] = mutation_result
                save_json(mutation_cache, mutation_cache_file)
                sentence = mutation_result["mutation_sentence"]
                protected_attributes = mutation_result["attributes"]
            except Exception as e:
                print(f"Error during mutation for sentence {i}: {e}")
                continue

    print(f"Protected attributes: {protected_attributes}")

    # Step 3: Make pairs + check validity
    if str(i) in pairs_cache:
        pairs = pairs_cache[str(i)]
        print("Read pairs from cache")
    else:
        try:
            pair_item = {"sentence": sentence, "attributes": protected_attributes}
            pairs_raw = call_openai(MAKE_PAIRS_PROMPT, pair_item)
            verified_pairs = []
            for p in pairs_raw["sentence_pairs"]:
                verify_item = {
                    "sentences": p["sentences"],
                    "attribute": p["attribute"]
                }
                try:
                    validity = call_openai(ATTRIBUTE_PRESERVATION_VALIDATION_PROMPT, verify_item)
                    p["valid"] = validity["verdict"]
                except Exception as e:
                    print(f"Error validating pair for sentence {i}: {e}")
                    p["valid"] = False
                verified_pairs.append(p)

            pairs = {"sentence_pairs": verified_pairs}
            pairs_cache[str(i)] = pairs
            save_json(pairs_cache, pairs_cache_file)
        except Exception as e:
            print(f"Error generating pairs for sentence {i}: {e}")
            continue

    try:
        for pair in pairs["sentence_pairs"]:
            if not pair.get("valid") or pair.get("valid") == "invalid":
                continue
            paired_sentences.append({
                "sentences": pair["sentences"],
                "attribute": pair["attribute"],
                "original_index": i
            })
    except Exception as e:
        print(f"Error accessing sentence pairs for sentence {i}: {e}")
        continue

    for ii, pair in enumerate(paired_sentences):
        print(f"Processing sentence {i}, pair {ii}")

        sentence1, sentence2 = pair["sentences"]

        try:
            translation1 = translator_choice(sentence1)
            translation2 = translator_choice(sentence2)
        except Exception as e:
            print(f"Error translating sentences {i}, pair {ii}: {e}")
            continue

        fairness_item = {
            "original": [sentence1, sentence2],
            "protected_attribute": pair["attribute"],
            "translation": [translation1, translation2]
        }

        try:
            fairness_result = call_openai(FAIRNESS_EVALUATION_PROMPT, fairness_item)
        except Exception as e:
            print(f"Error evaluating fairness for sentence {i}, pair {ii}: {e}")
            continue

        potential_fairness = fairness_result["translation_fairness"]["overall_fairness"]
        description = fairness_result["translation_fairness"]["description"]
        reader_interpretation_shift = fairness_result["translation_fairness"]["reader_interpretation_shift"]
        final_fairness = ""

        regression_results=[]
        if potential_fairness == "fair":
            final_fairness = "fair"
        elif potential_fairness in ("unfair", "questionable"):
            print(f"Sentence {i}, pair {ii} needs regression checking")

            try:
                regression_pair_item = {"sentence": sentence, "protected_attributes": protected_attributes}
                regression_pairs = call_openai(REGRESSION_PAIR_GENERATION_PROMPT, regression_pair_item)
            except Exception as e:
                print(f"Error generating regression pairs for sentence {i}, pair {ii}: {e}")
                continue

            found_semantic_issue = False
            for regression_pair in regression_pairs["control_pairs"]:
                reg_sentence1, reg_sentence2 = regression_pair["sentences"]

                try:
                    reg_translation1 = translator_choice(reg_sentence1)
                    reg_translation2 = translator_choice(reg_sentence2)
                except Exception as e:
                    print(f"Error translating regression sentences for sentence {i}, pair {ii}: {e}")
                    continue

                regression_item = {
                    "sentences": [reg_sentence1, reg_sentence2],
                    "translations": [reg_translation1, reg_translation2],
                    "exact_change": regression_pair["exact_change"]
                }

                try:
                    regression_result = call_openai(TRANSLATION_STABILITY_PROMPT, regression_item)
                    regression_results.append({"regression_item":regression_item,"regression_result":regression_result})
                    if regression_result["verdict"] == "semantic_issue":
                        found_semantic_issue = True
                        break
                except Exception as e:
                    print(f"Error evaluating regression for sentence {i}, pair {ii}: {e}")
                    continue

            final_fairness = "fair" if found_semantic_issue else "unfair"

        print(f"Sentence {i} Pair {ii}, Final fairness: {final_fairness}")

        if final_fairness == "unfair":
            print(f"Attempting repair for sentence {i}, pair {ii}...")
            try:
                repair_input_data = {
                    "sentence1": sentence1,
                    "sentence2": sentence2,
                    "attribute": pair["attribute"],
                    "unfairness_description": description
                }

                repair_response = call_openai(REPAIR_PROMPT, repair_input_data)

                repaired_translation1 = repair_response.get("repaired_translation_1")
                repaired_translation2 = repair_response.get("repaired_translation_2")
                repair_strategy_notes = repair_response.get("repair_strategy_notes")
                repair_raw_response = repair_response

                if repaired_translation1 and repaired_translation2:
                    print(f"Repair successful for sentence {i}, pair {ii}")
                    print(f"  Repaired T1: {repaired_translation1}")
                    print(f"  Repaired T2: {repaired_translation2}")
                else:
                    print(f"Repair failed to return valid translations for sentence {i}, pair {ii}")
                    final_fairness = "unfair_repair_failed"

            except Exception as e:
                print(f"Error during repair for sentence {i}, pair {ii}: {e}")
                final_fairness = f"unfair_repair_error: {e}"


        results.append({
            "original_index": i,
            "final_fairness": final_fairness,
            "protected_attribute": pair["attribute"],
            "repaired_translation1": repaired_translation1,
            "repaired_translation2": repaired_translation2,
        })

        logs.append({
            "original_index": i,
            "protected_attribute": pair["attribute"],
            "potential_fairness": potential_fairness,
            "final_fairness": final_fairness,
            "reader_interpretation_shift": reader_interpretation_shift,
            "description": description,
            "original_sentence": sentence,
            "sentence1": sentence1,
            "sentence2": sentence2,
            "translation1": translation1,
            "translation2": translation2,
            "regression_pairs": regression_pairs if potential_fairness != "fair" else None,
            "regression_results": regression_results if potential_fairness != "fair" else None,
            "repaired_translation1": repaired_translation1,
            "repaired_translation2": repaired_translation2,
            "repair_strategy_notes": repair_strategy_notes
        })

        save_json(results, result_file)
        save_json(logs, log_file)

    main_progress.update(1)
