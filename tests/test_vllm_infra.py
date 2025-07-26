import pytest

from entity.infrastructure.vllm_infra import VLLMInfrastructure


def _get_llm_url() -> str | None:
    infra = VLLMInfrastructure(auto_install=False)
    if infra.health_check():
        return infra.base_url
    return None


if _get_llm_url() is None:
    pytest.skip("vLLM server not available", allow_module_level=True)


def test_vllm_health_check():
    url = _get_llm_url()
    if url is None:
        pytest.skip("vLLM server not available")
    infra = VLLMInfrastructure(base_url=url)
    assert infra.health_check()


@pytest.mark.asyncio
async def test_vllm_generate():
    url = _get_llm_url()
    if url is None:
        pytest.skip("vLLM server not available")
    infra = VLLMInfrastructure(base_url=url)
    out = await infra.generate("ping")
    assert out == "ping"
