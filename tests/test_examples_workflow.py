import asyncio

import pytest

from entity.workflow import Workflow, WorkflowExecutor


class DummyLLM:
    async def generate(self, prompt: str) -> str:  # pragma: no cover - example
        return "dummy reasoning"


@pytest.mark.asyncio
async def test_basic_example_workflow():
    wf = Workflow.from_yaml("examples/basic_workflow.yaml")
    resources = {"llm": DummyLLM()}
    executor = WorkflowExecutor(resources, wf.steps)

    result = await executor.run("2 + 2", user_id="test")
    assert result == "Result: 4"


@pytest.mark.asyncio
async def test_example_workflow_multiple_users():
    wf = Workflow.from_yaml("examples/basic_workflow.yaml")
    resources = {"llm": DummyLLM()}
    executor = WorkflowExecutor(resources, wf.steps)
    memory: dict[str, str] = {}

    await executor.run("1 + 1", user_id="a", memory=memory)
    await executor.run("2 + 2", user_id="b", memory=memory)

    assert memory["a:history"] == ["1 + 1"]
    assert memory["b:history"] == ["2 + 2"]
