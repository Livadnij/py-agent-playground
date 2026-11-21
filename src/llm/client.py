import logging

import httpx
from typing import Optional, List
from src.llm.transport import post, get
from src.llm.schema import LLMModel, LLMCompletionsRes
from src.llm.prompts import summary_prompt, summary_marker
from src.config import settings
from src.utils import paint
from dataclasses import dataclass


@dataclass
class ChatResult:
    text: str
    tokens_used: int
    usage_percent: float

class LLMClient:
    def __init__(self, client: httpx.AsyncClient, model_key: str, system_prompt: str):
        self.client = client
        self.model: Optional[LLMModel] = None 
        self.model_key = model_key
        self.system_prompt = system_prompt
        self.summary: Optional[str] = None
        self.history: List[dict[str, str]] = []


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
        history_first_half = self.history[: history_len // 2]
        history_second_half = self.history[history_len // 2 :]

        if (history_second_half[0]['role'] == 'assistant'):
            history_second_half_first_el = history_second_half.pop(0)
            history_first_half.append(history_second_half_first_el)

        history_lines_list = [f'{item['role']} : {item['content']}' for item in history_first_half]

        history_transcript = '\n'.join(history_lines_list)

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
            'max_tokens' : settings.LLM_SUMMARY_MAX_TOKENS,
            'temperature' : settings.LLM_SUMMARY_TEMPERATURE
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
        user_message = {'role': 'user', 'content': message}
        messages.append(user_message)

        body = {
            'model': self.model_key, 
            'messages': messages,
            'temperature' : settings.LLM_COMPLETION_TEMPERATURE
        }

        response_raw = await post(self.client, "/v1/chat/completions", body)
        response = LLMCompletionsRes.model_validate(response_raw)
        res_message = response.choices[0].message.content

        self.history.append(user_message)
        self.history.append({'role': 'assistant', 'content': res_message})

        if len(self.model.loaded_instances) == 0:
            await self._load_model_info()
            if len(self.model.loaded_instances) == 0:
                raise ValueError(f"Couldn't load model ({self.model_key}) to get its context_length")
            
        tokens_used = response.usage.prompt_tokens + response.usage.completion_tokens - response.usage.completion_tokens_details.reasoning_tokens
        usage_percent =  tokens_used * 100 / self.model.loaded_instances[0].config.context_length

        if(usage_percent >= settings.LLM_SUMMARY_THRESHOLD_PERCENT):
            try:
                await self.compact()
            except Exception:
                logging.exception('Compaction failed, history was left unchanged')
            
        return ChatResult(res_message, tokens_used, usage_percent)

    
    @classmethod
    async def create(cls, client, model_key, system_prompt):
        self = cls(client, model_key, system_prompt)
        await self._load_model_info()
        return self