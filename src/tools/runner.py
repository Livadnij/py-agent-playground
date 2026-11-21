from src.tools.basic import get_current_time


async def tool_runner(tool_name: str, args: str | None = None):
    if tool_name == "get_current_time":
        return await get_current_time()
    else:
        return "Unknown tool"