import asyncio
import logging

import httpx
from src.commands import COMMANDS
from src.config import settings
from src.llm.transport import post
from src.llm.client import LLMClient
from src.llm.prompts import system_prompt
from src.utils import paint

async def main():

    headers = {'Authorization': 'Bearer ' + settings.LLM_API_KEY}
    async with httpx.AsyncClient(headers=headers, base_url= settings.LLM_BASE_URL, timeout=settings.LLM_TIMEOUT) as client:
        llm_client = await LLMClient.create(client, settings.LLM_MODEL, system_prompt)
        print("write '/exit' or Ctrl + C to stop")

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
            if response.usage_percent < 37:
                percent_color = 'green'
            elif response.usage_percent > 37 and response.usage_percent < 70:
                percent_color = 'yellow'
            else: 
                percent_color = 'red'

            print("\n" + paint(f'{response.tokens_used} tokens used, {response.usage_percent:.0f} context percent used', percent_color) + "\n")
            print ('')



if __name__ == "__main__":
    # logging.basicConfig(
    #     level= logging.INFO if settings.PRODUCTION else logging.DEBUG,
    # )
    asyncio.run(main())