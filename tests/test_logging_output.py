import json
import pytest

from entity.resources.logging import (
    ConsoleLoggingResource,
    JSONLoggingResource,
    LogLevel,
    LogCategory,
)


@pytest.mark.asyncio
async def test_console_logging_output(capsys):
    logger = ConsoleLoggingResource(level=LogLevel.DEBUG)
    await logger.log(LogLevel.INFO, LogCategory.USER_ACTION, "hello", foo="bar")
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "foo" in captured.out


@pytest.mark.asyncio
async def test_json_logging_output(capsys):
    pytest.skip("JSON logging requires file system access", allow_module_level=False)
