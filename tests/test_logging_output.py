import json
import pytest
from entity.resources.logging import (
    RichConsoleLoggingResource,
    RichJSONLoggingResource,
    LogCategory,
    LogContext,
    LogLevel,
    RichLoggingResource,
)


@pytest.mark.asyncio
async def test_console_logging_output(capsys):
    logger = RichConsoleLoggingResource(level=LogLevel.DEBUG)
    await logger.log(
        LogLevel.INFO,
        LogCategory.USER_ACTION,
        "hello",
        LogContext(user_id="u"),
        foo="bar",
    )
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "foo" in captured.out


@pytest.mark.asyncio
async def test_json_logging_output(tmp_path):
    log_file = tmp_path / "log.json"
    logger = RichJSONLoggingResource(level=LogLevel.INFO, output_file=str(log_file))
    await logger.log(
        LogLevel.WARNING,
        LogCategory.ERROR,
        "oops",
        LogContext(user_id="u"),
        code=123,
    )
    data = json.loads(log_file.read_text())
    assert data["message"] == "oops"
    assert data["context"]["user_id"] == "u"
    assert data["fields"]["code"] == 123
