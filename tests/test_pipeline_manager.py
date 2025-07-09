import asyncio

from pipeline import (PipelineManager, PipelineStage, PluginRegistry,
                      PromptPlugin, SystemRegistries, ToolRegistry)

from entity.core.resources.container import ResourceContainer


class WaitPlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    async def _execute_impl(self, context):
        await asyncio.sleep(0.05)
        context.set_response("ok")


def make_manager():
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(WaitPlugin({}), PipelineStage.DELIVER)
    )
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    return PipelineManager(registries)


def test_pipeline_manager_active_flag():
    manager = make_manager()

    async def run_task():
        task = manager.start_pipeline("hi")
        assert manager.has_active_pipelines()
        res = await task
        return res

    result = asyncio.run(run_task())
    assert result == "ok"
    assert not manager.has_active_pipelines()


def test_pipeline_manager_active_count():
    manager = make_manager()

    async def run_task():
        task = manager.start_pipeline("hi")
        assert manager.active_pipeline_count() == 1
        res = await task
        return res

    result = asyncio.run(run_task())
    assert result == "ok"
    assert manager.active_pipeline_count() == 0


def test_start_pipeline_uses_new_event_loop(monkeypatch):
    manager = make_manager()

    real_new_event_loop = asyncio.new_event_loop
    called: dict[str, bool] = {}

    def fake_new_event_loop() -> asyncio.AbstractEventLoop:
        called["new_loop"] = True
        return real_new_event_loop()

    monkeypatch.setattr(
        asyncio, "get_running_loop", lambda: (_ for _ in ()).throw(RuntimeError)
    )
    monkeypatch.setattr(asyncio, "new_event_loop", fake_new_event_loop)

    task = manager.start_pipeline("hi")
    loop = task.get_loop()
    result = loop.run_until_complete(task)
    loop.close()

    assert result == "ok"
    assert called.get("new_loop") is True
