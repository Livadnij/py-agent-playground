import logging

import httpx
from typing import Optional, List, Any
from src.config import Settings
from src.llm.transport import post, get
from src.llm.schema import LLMModel, LLMCompletionsRes
from src.llm.prompts import summary_prompt, summary_marker
from src.utils import format_message, paint
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
            settings : Settings,
            tools: list[dict[str, Any]] | None = None, 
            tool_runner: Callable[[list[dict[str, Any]], str, str], Awaitable[str]] | None = None,
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
            if(model_raw['key'] == self.model_key):
                model = LLMModel.model_validate(model_raw)
                model_info.append(model) 
    
        if len(model_info) > 0 :
            self.model = model_info[0]
        else:
            raise ValueError(f"No models with provided key({self.model_key}) were found")


    async def compact(self):
        print (paint('Conversation compacting has begun', 'yellow'))

        summary_content = self.summary or ""
        history_len = len(self.history)
        history_mid = history_len // 2

        cut_index : int

        for i, item in enumerate(self.history[history_mid:], start=history_mid):
            if item['role'] == 'user':
                cut_index = i
                break
            elif i == history_len - 1 :
                cut_index = history_len

        history_first_half = self.history[: cut_index]
        history_second_half = self.history[cut_index :]

        history_transcript = '\n'.join(format_message(item) for item in history_first_half)

        messages = [
            {'role': 'system', 'content': summary_prompt}
        ]
        messages.append(
            {
                'role': 'user',
                'content': '<previous_summary>' + "\n" + summary_content + "\n" + '</previous_summary>' + "\n\n" + '<new_conversation>' + "\n" + history_transcript + "\n" + '</new_conversation>'
            }
        )

        body = {
            'model': self.model_key, 
            'messages': messages,
            'max_tokens' : self.settings.LLM_SUMMARY_MAX_TOKENS,
            'temperature' : self.settings.LLM_SUMMARY_TEMPERATURE
        }

        response_raw = await post(self.client, "/v1/chat/completions", body)
        response = LLMCompletionsRes.model_validate(response_raw)
        res_message = response.choices[0].message.content

        if res_message and response.choices[0].finish_reason != 'length':
            self.history = history_second_half
            self.summary = res_message
            print (paint('Conversation compacting has finished', 'yellow'))
        else :
            raise ValueError("Compacting returned an empty string.")


    async def chat(self, message: str) :
        system_content = self.system_prompt or ""
        summary_content = self.summary or ""

        if not summary_content: 
            full_system_prompt = system_content
        elif not system_content: 
            full_system_prompt = (
                summary_marker + "\n" + summary_content
            )
        else :
            full_system_prompt = (
                system_content + "\n" + summary_marker + "\n" + summary_content
            )
    
        messages = []

        if full_system_prompt:
            messages.append({'role': 'system', 'content': full_system_prompt})
        messages.extend(self.history)
       
        temp_messages = []
        user_message = {'role': 'user', 'content': message}
        temp_messages.append(user_message)

        iteration = 0

        while iteration <= self.settings.LLM_MAX_TOOL_ROUNDS:
            body = {
                'model': self.model_key,
                'messages': [*messages, *temp_messages],
                'temperature': self.settings.LLM_COMPLETION_TEMPERATURE,
            }

            if self.tools:
                body['tools'] = self.tools

            response_raw = await post(self.client, "/v1/chat/completions", body)
            res_message = response_raw['choices'][0]['message'].get('content')
            tool_calls = response_raw['choices'][0]['message'].get('tool_calls')

            if not tool_calls:
                temp_messages.append({'role': 'assistant', 'content': res_message})
                break

            temp_messages.append({'role': 'assistant', 'content': res_message, 'tool_calls': tool_calls})

            for call in tool_calls:
                tool_result = await self.tool_runner(self.tools, call['function']['name'], call['function']['arguments'])
                temp_messages.append({'role': 'tool', 'tool_call_id': call['id'], 'content': tool_result})

            iteration += 1
        else:
            raise ValueError('Tool round limit reached without a final answer')
        
        self.history.extend(temp_messages)

        response = LLMCompletionsRes.model_validate(response_raw)

        if len(self.model.loaded_instances) == 0:
            await self._load_model_info()
            if len(self.model.loaded_instances) == 0:
                raise ValueError(f"Couldn't load model ({self.model_key}) to get its context_length")
            
        tokens_used = response.usage.prompt_tokens + response.usage.completion_tokens - response.usage.completion_tokens_details.reasoning_tokens
        usage_percent =  tokens_used * 100 / self.model.loaded_instances[0].config.context_length

        if(usage_percent >= self.settings.LLM_SUMMARY_THRESHOLD_PERCENT):
            try:
                await self.compact()
            except Exception as e:
                logging.exception(f'Compaction failed, history was left unchanged.\nerror: {e}')
            
        return ChatResult(res_message, tokens_used, usage_percent)

    
    @classmethod
    async def create(cls, client, model_key, system_prompt, settings, tools, tool_runner):
        self = cls(client, model_key, system_prompt, settings, tools, tool_runner)
        await self._load_model_info()
        return self