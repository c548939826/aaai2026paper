from tqdm import tqdm
import openai
import sys
import os
import re

flag = sys.argv[1]
base_dir = f"../../experiments/{flag}/country"

match = re.search(r'_(gpt4omini|gpt4o|gemini|deepseek|google)$', flag)
translator_name = match.group(1) if match else "gpt4omini"

TRANSLATION_PROMPT = """
Translation this sentence into Chinese.
Return only the translated sentence without any other mark or sentence.
"""

client = openai.OpenAI(
    base_url=" ",
    api_key=" "
)
def gpt4omini_translator(sentence):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": TRANSLATION_PROMPT},
                  {"role": "user", "content": sentence}],
        temperature=0.3,
    ).choices[0].message.content.strip()

def gpt4o_translator(sentence):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": TRANSLATION_PROMPT},
                  {"role": "user", "content": sentence}],
        temperature=0.3,
    ).choices[0].message.content.strip()

def gemini_translator(sentence):
    return client.chat.completions.create(
        model="gemini-1.5-flash-8b",
        messages=[{"role": "system", "content": TRANSLATION_PROMPT},
                  {"role": "user", "content": sentence}],
        temperature=0.3,
    ).choices[0].message.content.strip()

def deepseek_translator(sentence):
    return client.chat.completions.create(
        model="deepseek-v3-250324",
        messages=[{"role": "system", "content": TRANSLATION_PROMPT},
                  {"role": "user", "content": sentence}],
        temperature=0.3,
    ).choices[0].message.content.strip()

translator_fn_map = {
    "gpt4omini": gpt4omini_translator,
    "gpt4o": gpt4o_translator,
    "gemini": gemini_translator,
    "deepseek": deepseek_translator,
    "google": google_translator,
}
translator_fn = translator_fn_map[translator_name]

en_file = os.path.join(base_dir, "en_mu.txt")
with open(en_file, "r", encoding="utf-8") as f:
    enlines = [line.strip() for line in f if line.strip()]
    
enlines = [enline.replace("\t".join(enline.split("\t")[:2]) + '\t', "").strip() for enline in enlines]

lookup_file = os.path.join(base_dir, "LookUpTable.txt")
dic = {}
try:
    with open(lookup_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f]
        dic = dict(zip(lines[::2], lines[1::2]))
except FileNotFoundError:
    pass

out_file = os.path.join(base_dir, "f_en_mu.zh.beam")
candi_file = os.path.join(base_dir, "candidata.en")

with open(out_file, "w", encoding="utf-8") as f_out, \
     open(candi_file, "w", encoding="utf-8") as f_candi:

    for line in tqdm(enlines):
        if line not in dic or dic[line] == "":
            try:
                trans = translator_fn(line)
                if trans == "":
                    trans = deepseek_translator(line)
            except Exception as e:
                try:
                    trans = deepseek_translator(line)
                except Exception as e2:
                    trans = ""
            
            dic[line] = trans
            f_candi.write(line + "\n")

        f_out.write(dic[line] + "\n")

with open(lookup_file, "w", encoding="utf-8") as f_dic:
    for k, v in dic.items():
        f_dic.write(k + "\n")
        f_dic.write(v + "\n")
