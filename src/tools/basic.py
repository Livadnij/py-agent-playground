from datetime import datetime

from src.tools.registry import tool


@tool('Returns the current local date and time in ISO format. Use when the user asks for the date or time.')
async def get_current_time():
    now = datetime.now().astimezone()
    return now.isoformat()


