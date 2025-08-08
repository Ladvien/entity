import pytest

from entity.infrastructure.vllm_infra import VLLMInfrastructure


@pytest.mark.asyncio
async def test_vllm_health_check():
    infra = VLLMInfrastructure()
    is_healthy = await infra.health_check()
    if not is_healthy:
        pytest.skip("vLLM server not available")
    assert is_healthy


@pytest.mark.asyncio
async def test_vllm_generate():
    infra = VLLMInfrastructure()
    if not infra.health_check_sync():
        pytest.skip("vLLM server not available")
    
    # Try to generate, but skip if vLLM isn't actually running
    try:
        out = await infra.generate("ping")
        assert isinstance(out, str) and len(out) > 0
    except Exception as e:
        # If we can't connect, vLLM isn't running
        if "connection" in str(e).lower() or "connect" in str(e).lower():
            pytest.skip("vLLM server not running")
        raise
