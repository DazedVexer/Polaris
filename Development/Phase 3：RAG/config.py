import os            
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).parent
RULES_DIR = BASE_DIR / "rules"
SESSIONS_DIR = BASE_DIR / "sessions"

LTM_DB_PATH = BASE_DIR / "polaris_memory.db"

load_dotenv(BASE_DIR / ".env", override=True)
LLM_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "base_url": os.getenv("OPENAI_BASE_URL"),
    "model": os.getenv("OPENAI_MODEL"),
    "temperature": 0.7,
    "max_tokens": 2000,
}

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

STM_WindowSize = 10
STM_SUMMARY_TRIGGER = 18

LTM_RETRIEVAL_K = 5

LLM_MEMORY_EXTRACTION = 5

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

BGE_MODEL_NAME = os.getenv("BGE_MODEL_NAME", "BAAI/bge-small-zh-v1.5")

VECTOR_DB_PROVIDER = os.getenv("VECTOR_DB_PROVIDER", "chroma")

CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"

FAISS_INDEX_PATH = BASE_DIR / "faiss_index.bin"
FAISS_META_PATH = BASE_DIR / "faiss_meta.json"

VECTOR_SIMILARITY_THRESHOLD = 0.65

MEMORY_RETRIEVAL_TOP_K = 5

KB_DIR = BASE_DIR / "kb"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

KB_RETRIEVAL_TOP_K = 3
