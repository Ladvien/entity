import json
import pytest

from entity.resources.logging import (
    RichConsoleLoggingResource,
    RichJSONLoggingResource,
    LogLevel,
    LogCategory,
)


@pytest.mark.asyncio
async def test_console_logging_output(capsys):
    logger = RichConsoleLoggingResource(level=LogLevel.DEBUG)
    await logger.log(LogLevel.INFO, LogCategory.USER_ACTION, "hello", foo="bar")
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "foo" in captured.out


@pytest.mark.asyncio
async def test_json_logging_output(capsys):
    logger = RichJSONLoggingResource(level=LogLevel.DEBUG)
    await logger.log(LogLevel.WARNING, LogCategory.ERROR, "oops", code=123)
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())
    assert data["message"] == "oops"
    assert data["fields"]["code"] == 123
