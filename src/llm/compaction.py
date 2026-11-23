from typing import Any

from httpx import AsyncClient

from src.config import Settings
from src.llm.schema import LLMCompletionsRes
from src.llm.transport import post
from src.utils import format_message


def find_cut_index (history: list[dict[str, Any]]) -> int :  
    history_len = len(history)
    history_mid = history_len // 2

    for i, item in enumerate(history[history_mid:], start=history_mid):
        if item['role'] == 'user':
            return i

    return history_len


def build_summary_messages (history: list[dict[str, Any]], summary_prompt: str, summary: str | None) -> list[dict[str, Any]] :
    history_transcript = '\n'.join(format_message(item) for item in history)
    summary_content = summary or ""

    messages = [
        {'role': 'system', 'content': summary_prompt}
    ]
    messages.append(
        {
            'role': 'user',
            'content': '<previous_summary>' + "\n" + summary_content + "\n" + '</previous_summary>' + "\n\n" + '<new_conversation>' + "\n" + history_transcript + "\n" + '</new_conversation>'
        }
    )
    return messages

async def summarize (http_client: AsyncClient, model_key: str, messages: list[dict[str, Any]], settings: Settings, ) -> LLMCompletionsRes:
    body = {
        'model': model_key, 
        'messages': messages,
        'max_tokens' : settings.LLM_SUMMARY_MAX_TOKENS,
        'temperature' : settings.LLM_SUMMARY_TEMPERATURE
    }
    
    response_raw = await post(http_client, "/v1/chat/completions", body)
    response = LLMCompletionsRes.model_validate(response_raw)

    return response