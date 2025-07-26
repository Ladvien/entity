import pytest

from entity.workflow import Workflow, WorkflowExecutor
from entity.resources.memory import Memory
from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.infrastructure.vllm_infra import VLLMInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure


def _get_llm():
    vllm = VLLMInfrastructure(auto_install=False)
    if vllm.health_check():
        return vllm
    ollama = OllamaInfrastructure(
        "http://localhost:11434",
        "llama3.2:3b",
        auto_install=False,
    )
    if ollama.health_check():
        return ollama
    return None


if _get_llm() is None:
    pytest.skip("No LLM infrastructure available", allow_module_level=True)


@pytest.mark.asyncio
async def test_basic_example_workflow():
    llm_infra = _get_llm()
    pytest.skip(
        "Workflow depends on deterministic LLM output", allow_module_level=False
    )
    wf = Workflow.from_yaml("examples/basic_workflow.yaml")
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    resources = {"llm": llm_infra, "memory": memory}
    executor = WorkflowExecutor(resources, wf.steps)

    result = await executor.execute("2 + 2", user_id="test")
    assert result == "Result: 4"


@pytest.mark.asyncio
async def test_example_workflow_multiple_users():
    llm_infra = _get_llm()
    pytest.skip(
        "Workflow depends on deterministic LLM output", allow_module_level=False
    )
    wf = Workflow.from_yaml("examples/basic_workflow.yaml")
    resources = {"llm": llm_infra}
    executor = WorkflowExecutor(resources, wf.steps)
    infra = DuckDBInfrastructure(":memory:")
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))

    await executor.execute("1 + 1", user_id="a", memory=memory)
    await executor.execute("2 + 2", user_id="b", memory=memory)

    assert await memory.load("a:history") == ["1 + 1"]
    assert await memory.load("b:history") == ["2 + 2"]
