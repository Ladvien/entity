import asyncio

import httpx

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.resources import ResourceContainer
from plugins.builtin.adapters import HTTPAdapter


class RespPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        first = context.get_conversation_history()[0]
        context.set_response({"msg": first.content})


def make_adapter(config=None):
    plugins = PluginRegistry()
    asyncio.run(plugins.register_plugin_for_stage(RespPlugin({}), PipelineStage.DO))
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    manager = PipelineManager(registries)
    return HTTPAdapter(manager, config)


def test_http_adapter_basic():
    adapter = make_adapter()

    # ensure the adapter participates in both input and output stages
    assert HTTPAdapter.stages == [PipelineStage.PARSE, PipelineStage.DELIVER]

    async def _make_request():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=adapter.app),
            base_url="http://testserver",
        ) as client:
            resp = await client.post("/", json={"message": "hello"})
            assert resp.status_code == 200
            assert resp.json() == {"msg": "hello"}

    asyncio.run(_make_request())


def test_http_adapter_token_auth(tmp_path):
    cfg = {
        "auth_tokens": ["secret"],
        "audit_log_path": str(tmp_path / "audit.log"),
    }
    adapter = make_adapter(cfg)

    async def _request():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=adapter.app),
            base_url="http://testserver",
        ) as client:
            resp = await client.post("/", json={"message": "hi"})
            assert resp.status_code == 401

    asyncio.run(_request())
    assert "invalid token" in (tmp_path / "audit.log").read_text().lower()


def test_http_adapter_rate_limit(tmp_path):
    cfg = {
        "auth_tokens": ["secret"],
        "rate_limit": {"requests": 1, "interval": 60},
        "audit_log_path": str(tmp_path / "audit.log"),
    }
    adapter = make_adapter(cfg)

    async def _requests():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=adapter.app),
            base_url="http://testserver",
            headers={"Authorization": "Bearer secret"},
        ) as client:
            await client.post("/", json={"message": "hi"})
            resp = await client.post("/", json={"message": "hi"})
            assert resp.status_code == 429

    asyncio.run(_requests())
    assert "rate limit" in (tmp_path / "audit.log").read_text().lower()


def test_http_adapter_dashboard():
    adapter = make_adapter({"dashboard": True})

    async def _requests():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=adapter.app),
            base_url="http://testserver",
        ) as client:
            await client.post("/", json={"message": "hi"})
            resp = await client.get("/dashboard")
            assert resp.status_code == 200
            assert resp.json() == {"active_pipelines": 0}

    asyncio.run(_requests())
