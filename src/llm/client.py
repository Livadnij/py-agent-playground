import logging

import httpx
from typing import Optional, List, Any
from src.config import Settings
from src.llm.usage import calculate_usage
from src.llm.compaction import build_summary_messages, find_cut_index, summarize
from src.llm.prompting import build_system_prompt
from src.llm.tool_loop import run_tool_loop
from src.llm.transport import get
from src.llm.schema import LLMModel, LLMCompletionsRes
from src.llm.prompts import summary_prompt
from src.utils import paint
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass
class ChatResult:
    text: str
    tokens_used: int
    usage_percent: float


class LLMClient:
    def __init__(
        self,
        client: httpx.AsyncClient,
        model_key: str,
        system_prompt: str,
        settings: Settings,
        tools: list[dict[str, Any]] | None = None,
        tool_runner: (
            Callable[[list[dict[str, Any]], str, str], Awaitable[str]] | None
        ) = None,
        
    ):
        self.client = client
        self.model: Optional[LLMModel] = None
        self.model_key = model_key
        self.system_prompt = system_prompt
        self.summary: Optional[str] = None
        self.history: List[dict[str, str]] = []
        self.tools = tools
        self.tool_runner = tool_runner
        self.settings = settings

    async def _load_model_info(self):
        response = await get(self.client, "/api/v1/models")
        model_info: List[dict] = []
        for model_raw in response["models"]:
            if model_raw["key"] == self.model_key:
                model = LLMModel.model_validate(model_raw)
                model_info.append(model)

        if len(model_info) > 0:
            self.model = model_info[0]
        else:
            raise ValueError(
                f"No models with provided key({self.model_key}) were found"
            )

    async def compact(self):
        print(paint("Conversation compacting has begun", "yellow"))

        cut_index = find_cut_index(self.history)

        if cut_index == 0:
            print(paint("History cant be compacted. Nothing to compact yet.", "yellow"))
            return

        history_first_half = self.history[:cut_index]
        history_second_half = self.history[cut_index:]

        messages = build_summary_messages(
            history_first_half, summary_prompt, self.summary
        )

        response = await summarize(self.client, self.model_key, messages, self.settings)
        res_message = response.choices[0].message.content

        if res_message and response.choices[0].finish_reason != "length":
            self.history = history_second_half
            self.summary = res_message
            print(paint("Conversation compacting has finished", "yellow"))
        else:
            raise ValueError("Compacting returned an empty string.")

    async def chat(self, message: str):
        full_system_prompt = build_system_prompt(self.system_prompt, self.summary)

        messages = []

        if full_system_prompt:
            messages.append({"role": "system", "content": full_system_prompt})
        messages.extend(self.history)

        temp_messages = []

        response_raw = await run_tool_loop(
            self.client,
            self.settings,
            self.model_key,
            temp_messages,
            message,
            messages,
            self.tools,
            self.tool_runner,
        )

        self.history.extend(temp_messages)

        response = LLMCompletionsRes.model_validate(response_raw)
        res_message = response.choices[0].message.content

        if len(self.model.loaded_instances) == 0:
            await self._load_model_info()
            if len(self.model.loaded_instances) == 0:
                raise ValueError(
                    f"Couldn't load model ({self.model_key}) to get its context_length"
                )

        usage = calculate_usage(
            response, self.model.loaded_instances[0].config.context_length
        )

        if usage.usage_percent >= self.settings.LLM_SUMMARY_THRESHOLD_PERCENT:
            try:
                await self.compact()
            except Exception as e:
                logging.exception(
                    f"Compaction failed, history was left unchanged.\nerror: {e}"
                )

        return ChatResult(
            res_message, usage.tokens_used, usage.usage_percent
        )

    @classmethod
    async def create(
        cls, client, model_key, system_prompt, settings, tools, tool_runner
    ):
        self = cls(client, model_key, system_prompt, settings, tools, tool_runner)
        await self._load_model_info()
        return self
