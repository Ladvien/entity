import asyncio

from pipeline import (
    PipelineManager,
    PipelineStage,
    PluginRegistry,
    PromptPlugin,
    SystemRegistries,
    ToolRegistry,
)
from pipeline.state import PipelineState


class StateManager:
    def __init__(self, max_states: int = 1) -> None:
        self.max_states = max_states
        self._states: dict[str, "PipelineState"] = {}

    async def save_state(self, state: "PipelineState") -> None:
        if len(self._states) >= self.max_states:
            oldest = next(iter(self._states))
            self._states.pop(oldest)
        self._states[state.pipeline_id] = state.snapshot()

    async def load_state(self, pid: str):
        return self._states.get(pid)

    async def pipeline_ids(self):
        return list(self._states.keys())


from entity.core.resources.container import ResourceContainer


class SavePlugin(PromptPlugin):
    stages = [PipelineStage.DELIVER]

    def __init__(self, manager: StateManager) -> None:
        super().__init__({})
        self.manager = manager

    async def _execute_impl(self, context):
        await self.manager.save_state(context.state)
        context.set_response(context.state.pipeline_id)


def make_manager(manager: StateManager) -> PipelineManager:
    plugins = PluginRegistry()
    asyncio.run(
        plugins.register_plugin_for_stage(SavePlugin(manager), PipelineStage.DELIVER)
    )
    registries = SystemRegistries(ResourceContainer(), ToolRegistry(), plugins)
    return PipelineManager(registries)


def test_state_manager_concurrent_limit():
    state_manager = StateManager(max_states=2)
    manager = make_manager(state_manager)

    async def run_tasks():
        tasks = [manager.start_pipeline(str(i)) for i in range(3)]
        return await asyncio.gather(*tasks)

    ids = asyncio.run(run_tasks())
    stored_ids = asyncio.run(state_manager.pipeline_ids())
    assert len(stored_ids) == 2
    assert len(set(ids) - set(stored_ids)) >= 1
