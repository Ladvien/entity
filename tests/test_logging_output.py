import json
import pytest

from entity.resources.logging import RichLoggingResource, LogLevel, LogCategory


@pytest.mark.asyncio
async def test_console_logging_output(capsys):
    logger = RichLoggingResource(level=LogLevel.DEBUG)
    await logger.log(LogLevel.INFO, LogCategory.USER_ACTION, "hello", foo="bar")
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "foo" in captured.out


@pytest.mark.asyncio
async def test_json_logging_output(tmp_path):
    log_file = tmp_path / "log.json"
    logger = RichLoggingResource(
        level=LogLevel.DEBUG, json=True, log_file=str(log_file)
    )
    await logger.log(LogLevel.WARNING, LogCategory.ERROR, "oops", code=123)
    data = json.loads(log_file.read_text().splitlines()[0])
    assert data["message"] == "oops"
    assert data["fields"]["code"] == 123
