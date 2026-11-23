import asyncio

from httpx import AsyncClient
from typing import Any
from collections.abc import Awaitable, Callable

from src.llm.transport import post
from src.config import Settings


async def run_tool_loop(
    http_client: AsyncClient,
    settings: Settings,
    model_key: str,
    temp_messages: list[dict[str, Any]],
    message: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_runner: (
        Callable[[list[dict[str, Any]], str, str], Awaitable[str]] | None
    ) = None,
):

    user_message = {"role": "user", "content": message}
    temp_messages.append(user_message)
    iteration = 0
    last_signature = None
    repeat_count = 0

    while iteration < settings.LLM_MAX_TOOL_ROUNDS:
        body = {
            "model": model_key,
            "messages": [*messages, *temp_messages],
            "temperature": settings.LLM_COMPLETION_TEMPERATURE,
        }

        if tools:
            body["tools"] = tools

        response_raw = await post(http_client, "/v1/chat/completions", body)
        res_message = response_raw["choices"][0]["message"].get("content")
        tool_calls = response_raw["choices"][0]["message"].get("tool_calls")

        if not tool_calls:
            temp_messages.append({"role": "assistant", "content": res_message})
            break

        signature = tuple(
            (c["function"]["name"], c["function"]["arguments"]) for c in tool_calls
        )

        if signature == last_signature:
            repeat_count += 1
        else:
            repeat_count = 1
            last_signature = signature

        if repeat_count > settings.LLM_MAX_IDENTICAL_CALLS + 1:
            raise ValueError("Model keeps repeating the same tool call")

        if iteration == settings.LLM_MAX_TOOL_ROUNDS - 1:
            raise ValueError("Tool round limit reached without a final answer")

        repeated = repeat_count > settings.LLM_MAX_IDENTICAL_CALLS

        temp_messages.append(
            {"role": "assistant", "content": res_message, "tool_calls": tool_calls}
        )

        async def run_call(call):
            if repeated:
                return "You already made this exact call. Try something different."
            return await tool_runner(
                tools, call["function"]["name"], call["function"]["arguments"]
            )

        results = await asyncio.gather(*(run_call(call) for call in tool_calls))

        for call, result in zip(tool_calls, results):
            temp_messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": result}
            )

        iteration += 1
    else:
        raise ValueError("Tool round limit reached without a final answer")

    return response_raw
