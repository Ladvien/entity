import asyncio

import httpx

from app import create_app
from pipeline import Agent


def test_fastapi_wrapper():
    agent = Agent()
    app = create_app(agent)

    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            resp = await client.post("/", json={"message": "ping"})
            assert resp.status_code == 200
            assert resp.json().get("message")

    asyncio.run(_run())
