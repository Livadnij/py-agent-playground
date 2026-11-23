import asyncio
from functools import partial
import logging

from httpx import AsyncClient

from src.config import Settings
from src.roles import ROLES
from src.tools.builder import tools_builder
from src.llm.client import LLMClient
from src.tools.runner import tool_runner
from src.tools.context import ToolContext

ROLE_LIMITS = {
    name: asyncio.Semaphore(data["max_instances"]) for name, data in ROLES.items()
}


async def client_factory(
    role: str,
    http_client: AsyncClient,
    settings: Settings,
):
    role_data = ROLES[role]
    system_prompt = role_data["system_prompt"]
    tools = tools_builder(role_data["tools"])
    model = role_data["model"]

    async def spawn(target_role: str, task: str) -> str:
        if target_role not in role_data["allowed_delegates"]:

            return f"Role '{target_role}' is not allowed. Allowed roles are {role_data['allowed_delegates']}"
        try:
            async with ROLE_LIMITS[target_role]:
                child = await client_factory(target_role, http_client, settings)
                result = await child.chat(task)
            if not result.text:
                return f"Sub-agent '{target_role}' after performing '{task}' task returned empty message."
        except Exception as e:
            message = f"While '{target_role}' sub-agent was running '{task}' task, error happened {type(e).__name__}: {e}."
            logging.exception(message)
            return message
        return result.text

    delegates = {
        name: ROLES[name]["description"] for name in role_data["allowed_delegates"]
    }

    ctx = ToolContext(role, delegates, spawn)
    runner = partial(tool_runner, ctx)

    return await LLMClient.create(
        http_client, model, system_prompt, settings, tools, runner
    )
