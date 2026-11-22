from httpx import AsyncClient

from src.config import Settings
from src.roles import ROLES
from src.tools.builder import tools_builder
from src.llm.client import LLMClient
from src.tools.runner import tool_runner


async def client_factory (
        role: str, 
        http_client: AsyncClient, 
        settings: Settings, 
        ):
    role_data = ROLES[role]
    system_prompt = role_data['system_prompt']
    tools = tools_builder(role_data['tools'])
    model = role_data['model']

    return await LLMClient.create(http_client, model, system_prompt, settings, tools, tool_runner)
