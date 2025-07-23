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
