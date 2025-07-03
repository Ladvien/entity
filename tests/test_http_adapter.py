import asyncio

import httpx

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    ResourceRegistry,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.adapters import HTTPAdapter
from pipeline.base_plugins import ResourcePlugin


class RespPlugin(PromptPlugin):
    stages = [PipelineStage.DO]

    async def _execute_impl(self, context):
        first = context.get_conversation_history()[0]
        context.set_response({"msg": first.content})


def make_adapter():
    plugins = PluginRegistry()
    plugins.register_plugin_for_stage(RespPlugin({}), PipelineStage.DO)
    registries = SystemRegistries(ResourceRegistry(), ToolRegistry(), plugins)
    manager = PipelineManager(registries)
    return HTTPAdapter(manager)


class HealthyResource(ResourcePlugin):
    stages = [PipelineStage.PARSE]

    async def health_check(self) -> bool:  # pragma: no cover - simple override
        return True

    async def _execute_impl(self, context):  # pragma: no cover - unused
        pass


class FailingResource(ResourcePlugin):
    stages = [PipelineStage.PARSE]

    async def health_check(self) -> bool:  # pragma: no cover - simple override
        return False

    async def _execute_impl(self, context):  # pragma: no cover - unused
        pass


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


def test_health_endpoint_reports_status():
    adapter = make_adapter()
    adapter._registries.resources.add("good", HealthyResource({}))

    async def _check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=adapter.app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "healthy"

    asyncio.run(_check())


def test_unhealthy_resources_flagged():
    adapter = make_adapter()
    adapter._registries.resources.add("bad", FailingResource({}))

    async def _check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=adapter.app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get("/health")
            data = resp.json()
            assert data["status"] == "unhealthy"
            assert not data["resources"]["bad"]

    asyncio.run(_check())


def test_metrics_endpoint_exposes_prometheus():
    adapter = make_adapter()
    adapter._registries.resources.add("good", HealthyResource({}))

    async def _check():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=adapter.app),
            base_url="http://testserver",
        ) as client:
            await client.post("/", json={"message": "ping"})
            metrics = await client.get("/metrics")
            assert metrics.status_code == 200
            assert b"requests_total" in metrics.content

    asyncio.run(_check())
