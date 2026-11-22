import asyncio
import logging
import httpx

from src.startup import startup
from src.repl import repl
from src.config import settings
from src.factory import client_factory


async def main():
    startup()
    
    headers = {'Authorization': 'Bearer ' + settings.LLM_API_KEY}
    async with httpx.AsyncClient(headers=headers, base_url= settings.LLM_BASE_URL, timeout=settings.LLM_TIMEOUT) as client:
        role = "orchestrator"
        llm_client = await client_factory(role, client, settings)
        print("write '/exit' or Ctrl + C to stop")
        await repl(llm_client)
        


if __name__ == "__main__":
    logging.basicConfig(
        level= logging.INFO if settings.PRODUCTION else logging.DEBUG,
    )
    asyncio.run(main())