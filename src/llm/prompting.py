from src.llm.prompts import summary_marker


def build_system_prompt(system: str, summary: str | None):
    system_prompt = system or ""
    summary_content = summary or ""

    if not summary_content:
        full_system_prompt = system_prompt
    elif not system_prompt:
        full_system_prompt = summary_marker + "\n" + summary_content
    else:
        full_system_prompt = (
            system_prompt + "\n" + summary_marker + "\n" + summary_content
        )

    return full_system_prompt
