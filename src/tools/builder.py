import logging

from src.tools.registry import TOOLS

def tools_builder (tools: list[str]) :
    tool_list = []
    for t in tools:
        tool = TOOLS.get(t)
        if tool:
            tool_list.append(tool['schema'])
        else:
            logging.error(f'Agent tool with the name {t} does not exist')
    return tool_list

