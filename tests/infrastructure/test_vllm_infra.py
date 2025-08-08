import pytest

from entity.infrastructure.vllm_infra import VLLMInfrastructure


def test_health_check_real():
    infra = VLLMInfrastructure()
    if not infra.health_check_sync():
        pytest.skip("vLLM server not available")
    assert infra.health_check_sync()
