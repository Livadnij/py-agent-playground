import inspect
import json
import logging

from src.roles import ROLES
from src.tools.registry import TOOLS

def validate_roles() : 
    for role, value in ROLES.items():
            for tool_name in value['tools']:
                tool = TOOLS.get(tool_name)
                if not tool :
                    logging.error(f"Role '{role}' lists tool '{tool_name}', but it is not registered")
                    continue
                if not inspect.iscoroutinefunction(tool["function"]):
                    logging.error(f"Function '{tool_name}' is not a coroutine.")

def startup ():
    validate_roles()
    for name, tool in TOOLS.items():
        logging.debug(f"{name}\n{json.dumps(tool['schema'], indent=2)}")