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


input_file = "./gender.txt"
base_name = os.path.basename(input_file)
input_file_name = os.path.splitext(base_name)[0]
output_dir = f"./output/{input_file_name}/{translator_name}"
os.makedirs(output_dir, exist_ok=True)

result_file = os.path.join(output_dir, "result_gender.json")
log_file = os.path.join(output_dir, "log_gender.json")

cache_dir = "./output/gender"
os.makedirs(cache_dir, exist_ok=True)

attribute_cache_file = os.path.join(cache_dir, "attribute_cache.json")
mutation_cache_file = os.path.join(cache_dir, "mutation_cache.json")
pairs_cache_file = os.path.join(cache_dir, "pairs_cache.json")
translation_cache_file = os.path.join(cache_dir, "translation_cache.json")


protected_attributes = "gender"

attribute_cache = load_json(attribute_cache_file) if os.path.exists(attribute_cache_file) else {}
mutation_cache = load_json(mutation_cache_file) if os.path.exists(mutation_cache_file) else {}
pairs_cache = load_json(pairs_cache_file) if os.path.exists(pairs_cache_file) else {}
translation_cache = load_json(translation_cache_file) if os.path.exists(translation_cache_file) else {}


results = load_json(result_file) if os.path.exists(result_file) else []
logs = load_json(log_file) if os.path.exists(log_file) else []

start_index = len(results)

original_sentences = []
with open(input_file, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if line.strip()]
    for line in lines:
        sentence = re.sub(r"^Gen:\s+(female|male)\s+", "", line).strip()
        original_sentences.append(sentence)

paired_sentences = []
for i in range(0, len(original_sentences), 2):
    if i + 1 < len(original_sentences):
        paired_sentences.append({
            "sentences": [original_sentences[i], original_sentences[i + 1]],
            "attribute": protected_attributes,
            "original_index": i // 2
        })


client = openai.OpenAI(
    base_url=" ",
    http_client=httpx.Client(transport=CustomTransport()),
    api_key=" "
)
saleclient = openai.OpenAI(
        base_url=" ",
        http_client=httpx.Client(transport=CustomTransport()),
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

def get_translation(sentence):
    if sentence in translation_cache:
        return translation_cache[sentence]
    else:
        translation = translator_choice(sentence)
        translation_cache[sentence] = translation
        save_json(translation_cache, translation_cache_file)
        return translation

total_pairs = len(paired_sentences)
main_progress = tqdm(
    total=total_pairs,
    initial=start_index,
    desc="Overall Progress",
    position=0,
    dynamic_ncols=True,
    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
)

for idx, pair_data in enumerate(paired_sentences[start_index:]):
    i = pair_data["original_index"]
    sentence1, sentence2 = pair_data["sentences"]

    print(f"Processing pair {i}:")
    print(f"  Sentence 1: {sentence1}")
    print(f"  Sentence 2: {sentence2}")

    try:
        translation1 = get_translation(sentence1)
        translation2 = get_translation(sentence2)
        print(f"  Translation 1: {translation1}")
        print(f"  Translation 2: {translation2}")
    except Exception as e:
        print(f"Error translating pair {i}: {e}")
        continue

    fairness_item = {
        "original": [sentence1, sentence2],
        "protected_attribute": pair_data["attribute"],
        "translation": [translation1, translation2]
    }

    try:
        fairness_result = call_openai(FAIRNESS_EVALUATION_PROMPT, fairness_item)
    except Exception as e:
        print(f"Error evaluating fairness for pair {i}: {e}")
        continue

    potential_fairness = fairness_result["translation_fairness"]["overall_fairness"]
    description = fairness_result["translation_fairness"]["description"]
    reader_interpretation_shift = fairness_result["translation_fairness"]["reader_interpretation_shift"]
    final_fairness = ""
    regression_results = []
    regression_pairs = None

    if potential_fairness == "fair":
        final_fairness = "fair"
    elif potential_fairness in ("unfair", "questionable"):
        print(f"Pair {i} needs regression checking")

        try:
            regression_pair_item = {"sentence": sentence1, "protected_attributes": [protected_attributes]}
            regression_pairs = call_openai(REGRESSION_PAIR_GENERATION_PROMPT, regression_pair_item)
        except Exception as e:
            print(f"Error generating regression pairs for pair {i}: {e}")
            continue

        found_semantic_issue = False
        if regression_pairs and "control_pairs" in regression_pairs:
            for regression_pair in regression_pairs["control_pairs"]:
                reg_sentence1, reg_sentence2 = regression_pair["sentences"]

                try:
                    reg_translation1 = get_translation(reg_sentence1)
                    reg_translation2 = get_translation(reg_sentence2)
                except Exception as e:
                    print(f"Error translating regression sentences for pair {i}: {e}")
                    continue

                regression_item = {
                    "sentences": [reg_sentence1, reg_sentence2],
                    "translations": [reg_translation1, reg_translation2],
                    "exact_change": regression_pair["exact_change"]
                }

                try:
                    regression_result = call_openai(TRANSLATION_STABILITY_PROMPT, regression_item)
                    regression_results.append({"regression_item": regression_item, "regression_result": regression_result})
                    if regression_result["verdict"] == "semantic_issue":
                        found_semantic_issue = True
                        break
                except Exception as e:
                    print(f"Error evaluating regression for pair {i}: {e}")
                    continue

        final_fairness = "fair" if found_semantic_issue else "unfair"

    print(f"Pair {i}, Final fairness: {final_fairness}")

    results.append({
        "original_index": i,
        "final_fairness": final_fairness,
        "protected_attribute": pair_data["attribute"],
        "translation1": translation1,
        "translation2": translation2,
    })

    logs.append({
        "original_index": i,
        "protected_attribute": pair_data["attribute"],
        "potential_fairness": potential_fairness,
        "final_fairness": final_fairness,
        "reader_interpretation_shift": reader_interpretation_shift,
        "description": description,
        "original_sentence": [sentence1, sentence2],
        "sentence1": sentence1,
        "sentence2": sentence2,
        "translation1": translation1,
        "translation2": translation2,
        "regression_pairs": regression_pairs,
        "regression_results": regression_results,
    })

    save_json(results, result_file)
    save_json(logs, log_file)

    main_progress.update(1)

main_progress.close()
print("Processing complete.")