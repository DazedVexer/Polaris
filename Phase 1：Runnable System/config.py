import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).parent
RULES_DIR = BASE_DIR / "rules"
SESSIONS_DIR = BASE_DIR / "sessions"

load_dotenv(BASE_DIR / ".env", override=True)
LLM_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "base_url": os.getenv("OPENAI_BASE_URL"),
    "model": os.getenv("OPENAI_MODEL"),
    "temperature": 0.6,
    "max_tokens": 2000,
}

STM_WindowSize = 10

def validate_config():
    errors = []
    if not LLM_CONFIG["api_key"]:
        errors.append("OPENAI_API_KEY 未设置，请在 .env 中配置")
    if not LLM_CONFIG["base_url"]:
        errors.append("OPENAI_BASE_URL 未设置")
    if not LLM_CONFIG["model"]:
        errors.append("OPENAI_MODEL 未设置")
    if errors:
        raise ValueError("\n".join(["\n❌ 配置错误："] + errors))
