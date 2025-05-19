import openai
TRANSLATION_PROMPT="""
Translation this sentence into chinese.
Return only the translated sentence without any other mark or sentence.
"""


client = openai.OpenAI(
        base_url=" ",
        api_key=" "
)

def gpt4o_translator(sentence):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": TRANSLATION_PROMPT},
            {"role": "user", "content": sentence}
        ],
        temperature=0.3,
    )
    return(response.choices[0].message.content)


def gemini_translator(sentence):
    response = client.chat.completions.create(
        model="gemini-1.5-flash-8b",
        messages=[
            {"role": "system", "content": TRANSLATION_PROMPT},
            {"role": "user", "content": sentence}
        ],
        temperature=0.3,
    )
    return(response.choices[0].message.content)

def deepseek_translator(sentence):
    response = client.chat.completions.create(
        model="deepseek-v3-250324",
        messages=[
            {"role": "system", "content": TRANSLATION_PROMPT},
            {"role": "user", "content": sentence}
        ],
        temperature=0.3,
    )
    return(response.choices[0].message.content)

def gpt4omini_translator(sentence):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": TRANSLATION_PROMPT},
            {"role": "user", "content": sentence}
        ],
        temperature=0.3,
    )
    return(response.choices[0].message.content)