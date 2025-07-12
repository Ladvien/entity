from entity.resources import LLM, Memory, Storage, StandardResources


def test_standard_resources_types() -> None:
    res = StandardResources(memory=Memory({}), llm=LLM({}), storage=Storage({}))
    assert isinstance(res.memory, Memory)
    assert isinstance(res.llm, LLM)
    assert isinstance(res.storage, Storage)
