from entity.resources import LLM, Memory, Storage, StandardResources


def test_standard_resources_types() -> None:
    res = StandardResources(
        memory=Memory(config={}),
        llm=LLM(config={}),
        storage=Storage(config={}),
    )
    assert isinstance(res.memory, Memory)
    assert isinstance(res.llm, LLM)
    assert isinstance(res.storage, Storage)
