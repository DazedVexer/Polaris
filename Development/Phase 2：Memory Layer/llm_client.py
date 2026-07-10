import time
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError
from config import LLM_CONFIG

_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"],
            timeout=30.0,
            max_retries=0
        )
    return _client

def chat_stream(messages: list[dict], max_retries: int = 3) -> str:
    last_error = None
    for attempt in range(max_retries):
        try:
            stream = _get_client().chat.completions.create(
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

        except (APIConnectionError, APITimeoutError) as e:
            last_error = e
            wait = 2 ** attempt
            time.sleep(wait)
        except RateLimitError as e:
            return f"[错误] API 调用频率过高，请稍后再试。"
        except APIError as e:
            return f"[错误] API 返回异常：{e}"
        except Exception as e:
            return f"[错误] {e}"

    return f"[错误] 重试 {max_retries} 次后仍然无法连接：{last_error}"