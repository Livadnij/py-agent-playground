from datetime import datetime

async def get_current_time():
    now = datetime.now().astimezone()
    return now.isoformat()


get_current_time_schema = {
    'type': 'function',
    'function': {
        'name': 'get_current_time',
        'description': 'Returns the current local date and time in ISO format. Use when the user asks for the date or time.',
        'parameters': {'type': 'object', 'properties': {}},
    },
}