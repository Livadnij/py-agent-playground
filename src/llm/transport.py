import httpx
from typing import Any

async def post(client: httpx.AsyncClient, route: str, body: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    response = await client.post(route, headers=headers, json=body)
    response.raise_for_status()
    return response.json()

async def get(client: httpx.AsyncClient, route: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    response = await client.get(route, headers=headers)
    response.raise_for_status()
    return response.json()