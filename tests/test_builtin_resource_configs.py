import pytest

from entity.resources.memory import Memory
from entity.resources.logging import LoggingResource
from entity.resources.llm import LLM
from entity.resources.storage import Storage


@pytest.mark.asyncio
async def test_memory_config_invalid():
    result = await Memory.validate_config({"kv_table": 123})
    assert not result.success


@pytest.mark.asyncio
async def test_logging_config_invalid():
    result = await LoggingResource.validate_config({"outputs": ""})
    assert not result.success


@pytest.mark.asyncio
async def test_llm_config_invalid():
    result = await LLM.validate_config({"provider": 123})
    assert not result.success


@pytest.mark.asyncio
async def test_storage_config_invalid():
    result = await Storage.validate_config({"namespace": 1})
    assert not result.success
