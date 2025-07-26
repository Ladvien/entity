import json
import pytest

from entity.resources.logging import ConsoleLoggingResource, JSONLoggingResource


@pytest.mark.asyncio
async def test_console_logging_output(capsys):
    logger = ConsoleLoggingResource(level="debug")
    await logger.log("info", "hello", foo="bar")
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "foo" in captured.out


@pytest.mark.asyncio
async def test_json_logging_output(capsys):
    logger = JSONLoggingResource(level="debug")
    await logger.log("warning", "oops", code=123)
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())
    assert data["message"] == "oops"
    assert data["fields"]["code"] == 123
