import asyncio

from src.commands import COMMANDS
from src.utils import paint

def usage_color(usage_percent: float)-> str :
    if usage_percent <= 37:
        return 'green'
    elif usage_percent < 70:
        return 'yellow'
    else: 
        return 'red'


async def repl(llm_client):
    while True:
        text = await asyncio.to_thread(input, '> ')
        print ('')
    
        if text.startswith('/'):
            name, _, args = text[1:].partition(' ')
            entry = COMMANDS.get(name)
            if entry is None:
                print('Unknown command, try /help')
                continue
            handler, _description = entry
            if await handler(llm_client, args):
                break
            continue
        response = await llm_client.chat(text)

        print (response.text)

        percent_color = usage_color(response.usage_percent)
    
        print("\n" + paint(f'{response.tokens_used} tokens used, {response.usage_percent:.0f} context percent used', percent_color) + "\n")