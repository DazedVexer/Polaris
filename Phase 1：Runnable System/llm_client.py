from openai import OpenAI
from config import LLM_CONFIG

client = OpenAI(
    api_key=LLM_CONFIG["api_key"],
    base_url=LLM_CONFIG["base_url"],
)

def chat_stream(messages: list[dict]):
    """流式调用 LLM，逐字打印回复"""
    stream = client.chat.completions.create(
        model=LLM_CONFIG["model"],
        messages=messages,
        temperature=LLM_CONFIG["temperature"],
        max_tokens=LLM_CONFIG["max_tokens"],
        stream=True,
    )
    full_response = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            print(text, end="", flush=True)
            full_response += text
    print()
    return full_response
