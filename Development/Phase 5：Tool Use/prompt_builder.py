from config import RULES_DIR

def sys_prompt_builder() -> str:
    if not RULES_DIR.exists():
        return "You are Polaris, a Personal AI Executive Assistant."

    prompt_list = []
    rule_files = sorted(RULES_DIR.glob("*.md"))
    for f in rule_files:
        prompt_list.append(f.read_text(encoding="utf-8"))

    prompt_string = ("\n---\n".join(prompt_list) +
                    "\n---\nYou are now interacting with users as Polaris. Please strictly adhere to all the rules above")

    return prompt_string
