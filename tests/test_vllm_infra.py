import pytest

from entity.infrastructure.vllm_infra import VLLMInfrastructure


def test_vllm_health_check(mock_vllm_server):
    infra = VLLMInfrastructure(base_url=mock_vllm_server)
    assert infra.health_check()


@pytest.mark.asyncio
async def test_vllm_generate(mock_vllm_server):
    infra = VLLMInfrastructure(base_url=mock_vllm_server)
    out = await infra.generate("ping")
    assert out == "ping"
