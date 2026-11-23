from typing import Annotated

from src.tools.context import ToolContext
from src.tools.registry import tool


@tool('Creates clean temporary agent, to which you can delefate tasks. You should use this tool to perform operation that are not available to you, or to delegate some work.')
async def delegate(
    ctx: ToolContext,
    role: Annotated[str, "Name of the agent that should be created"],
    task: Annotated[str, "A message to the agent"]
):
    return await ctx.spawn(role, task)


@tool('Returns a list of delegates agent can create and pass tasks to.')
async def list_allowed_delegates(ctx: ToolContext):
    return "\n".join(f"{name} - {desc}" for name, desc in ctx.delegates.items())