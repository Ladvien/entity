import pytest

from entity.infrastructure.vllm_infra import VLLMInfrastructure


@pytest.mark.asyncio
async def test_vllm_health_check():
    infra = VLLMInfrastructure()
    if not infra.health_check():
        pytest.skip("vLLM server not available")
    assert infra.health_check()


@pytest.mark.asyncio
async def test_vllm_generate():
    infra = VLLMInfrastructure()
    if not infra.health_check():
        pytest.skip("vLLM server not available")
    out = await infra.generate("ping")
    assert isinstance(out, str) and len(out) > 0
