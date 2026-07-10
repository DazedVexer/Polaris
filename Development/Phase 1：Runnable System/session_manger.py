import json
from datetime import datetime
from pathlib import Path
from config import SESSIONS_DIR

def create_session() -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_file = SESSIONS_DIR / f"{timestamp}.json"

    session_data = {
        "session_id": timestamp,
        "created_at": datetime.now().isoformat(),
        "messages": [],
    }
    session_file.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return session_file

def save_message(session_file: Path, role: str, content: str):
    try:
        data = json.loads(session_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        data = {"messages": []}

    data["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    })
    session_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_session(session_file: Path) -> list[dict]:
    try:
        return json.loads(session_file.read_text(encoding="utf-8")).get("messages", [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []
