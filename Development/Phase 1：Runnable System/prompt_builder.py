from config import RULES_DIR

def sys_prompt_builder(mode_hint: dict = None) -> str:
    """
    构建 system prompt。
    mode_hint 可选，用于后续 Phase 动态注入情绪模式指令。
    """
    if not RULES_DIR.exists():
        return "You are Polaris, a Personal AI Executive Assistant."

    prompt_list = []
    rule_files = sorted(RULES_DIR.glob("*.md"))
    for f in rule_files:
        prompt_list.append(f.read_text(encoding="utf-8"))

    base_prompt = ("\n---\n".join(prompt_list) +
                   "\n---\nYou are now interacting with users as Polaris. "
                   "Please strictly adhere to all the rules above.")

    return base_prompt
