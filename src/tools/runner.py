import json
import logging
from typing import Any

from src.tools.registry import TOOLS


async def tool_runner(allowed_tools: list[dict[str, Any]], tool_name: str, raw_args: str):
    allowed_tool_names = set((item['function']['name'] for item in allowed_tools))

    if (tool_name not in allowed_tool_names): return f"Tool with name '{tool_name}' does not exist"

    try:    
        args = json.loads(raw_args)
        tool = TOOLS.get(tool_name)
    
        if tool:
            return str(await tool['function'](**args))
        else:
            return f"Tool with name '{tool_name}' does not exist"
    except json.JSONDecodeError:
        return "Error happend while processing json."
    except TypeError:
        return "Missing or unexpected argument was provided."
    except Exception as e:
        logging.exception(f'Unhandled error: {e}')
        return "Unhandled error happened."

