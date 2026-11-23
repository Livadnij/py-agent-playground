from src.llm.schema import LLMCompletionsRes
from dataclasses import dataclass


@dataclass
class UsageResult:
    tokens_used: int
    usage_percent: float


def calculate_usage(response: LLMCompletionsRes, context_length: int):
    tokens_used = (
        response.usage.prompt_tokens
        + response.usage.completion_tokens
        - response.usage.completion_tokens_details.reasoning_tokens
    )
    usage_percent = (
        tokens_used * 100 / context_length
    )

    return UsageResult(tokens_used, usage_percent)