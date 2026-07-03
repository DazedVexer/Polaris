import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent

# 规则文件路径
RULES_DIR = BASE_DIR / "rules"

# LLM 配置
LLM_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "temperature": 0.7,
    "max_tokens": 2000,
}

# Session 存档路径
SESSIONS_DIR = BASE_DIR / "sessions"

# 短期记忆最大轮数
MAX_SHORT_TERM_TURNS = 10