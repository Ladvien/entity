import asyncio

import httpx

from entity import Agent
from app import create_app


def test_fastapi_wrapper():
    agent = Agent(llm="pipeline.plugins.resources.echo_llm:EchoLLMResource")
    app = create_app(agent)

    async def _run():
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post("/", json={"message": "ping"})
            assert resp.status_code == 200
            assert resp.json().get("message")

    asyncio.run(_run())
