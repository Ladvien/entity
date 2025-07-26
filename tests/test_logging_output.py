import json
import pytest

from entity.resources.logging import (
    RichConsoleLoggingResource,
    RichJSONLoggingResource,
)


@pytest.mark.asyncio
async def test_console_logging_output(capsys):
    logger = RichConsoleLoggingResource(level="debug")
    await logger.log("info", "hello", foo="bar")
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "foo" in captured.out


@pytest.mark.asyncio
async def test_json_logging_output(capsys):
    logger = RichJSONLoggingResource(level="debug")
    await logger.log("warning", "oops", code=123)
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())
    assert data["message"] == "oops"
    assert data["fields"]["code"] == 123
