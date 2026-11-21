from pydantic import BaseModel


class LoadedInstanceConfig(BaseModel):
    context_length: int
    parallel: int


class LoadedInstance(BaseModel):
    id: str
    config: LoadedInstanceConfig


class LLMModel(BaseModel):
    key: str
    max_context_length: int
    loaded_instances: list[LoadedInstance]


class Message(BaseModel):
    role: str
    content: str


class Choice(BaseModel):
    message: Message
    finish_reason: str


class CompletionTokensDetails(BaseModel):
    reasoning_tokens: int = 0


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    completion_tokens_details: CompletionTokensDetails = CompletionTokensDetails()


class LLMCompletionsRes(BaseModel):
    choices: list[Choice]
    usage: Usage

'''
{
  "id": "chatcmpl-dd3ztqi2dske2a4g4jd7d",
  "object": "chat.completion",
  "created": 1795204019,
  "model": "google/gemma-4-e4b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today? 😊",
        "reasoning_content": "",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 18,
    "completion_tokens": 11,
    "total_tokens": 29,
    "completion_tokens_details": {
      "reasoning_tokens": 0
    }
  },
  "stats": {},
  "system_fingerprint": "google/gemma-4-e4b"
}
'''

'''
{
      "type": "llm",
      "publisher": "unsloth",
      "key": "qwen3.8-27b",
      "display_name": "Qwen3.8 27B UD",
      "architecture": "qwen35",
      "quantization": {
        "name": "Q3_K_XL",
        "bits_per_weight": 3
      },
      "size_bytes": 14074004752,
      "params_string": "27B",
      "loaded_instances": 
      [ 
        {
            "id": "google/gemma-4-e4b",
            "config": {
                "context_length": 16128,
                "eval_batch_size": 2048,
                "physical_batch_size": 512,
                "parallel": 6,
                "flash_attention": true,
                "context_checkpoints": 32,
                "reasoning_budget_message": "",
                "speculative_draft_mtp": false,
                "speculative_draft_simple": false,
                "speculative_draft_model": "",
                "speculative_draft_max_tokens": 3,
                "speculative_draft_min_tokens": 0,
                "speculative_draft_min_continue_probability": 0,
                "offload_kv_cache_to_gpu": true
            },
            "remaining_ttl_seconds": 594
        }
        ],
      "max_context_length": 262144,
      "format": "gguf",
      "capabilities": {
        "vision": true,
        "trained_for_tool_use": true,
        "reasoning": {
          "allowed_options": [
            "off",
            "on"
          ],
          "default": "on"
        }
      },
      "description": null
      "variants": [
        "google/gemma-4-e4b@q4_k_m"
      ],
      "selected_variant": "google/gemma-4-e4b@q4_k_m"
},
'''

