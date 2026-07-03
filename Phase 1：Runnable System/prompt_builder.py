from pathlib import Path
from config import RULES_DIR

def build_system_prompt() -> str:
    if not RULES_DIR.exists():
        return "You are CompassY, a Personal AI Executive Assistant."

    prompt_parts = []
    # 按文件名排序读取
    rule_files = sorted(RULES_DIR.glob("*.md"))

    for f in rule_files:
            content = f.read_text(encoding="utf-8")
            prompt_parts.append(content)


    full_prompt = ("\n\n---\n\n".join(prompt_parts) +
                   "\n\n---\n\nYou are now interacting with users as CompassY."
                   "Please strictly adhere to all the rules above.")

    return full_prompt