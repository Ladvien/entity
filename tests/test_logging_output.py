import json
import pytest
<<<<<<< HEAD
from entity.resources.logging import (
<<<<<<< HEAD
    RichConsoleLoggingResource,
    RichJSONLoggingResource,
    LogLevel,
    LogCategory,
=======
    LogCategory,
    LogLevel,
    RichConsoleLoggingResource,
    RichJSONLoggingResource,
>>>>>>> pr-1962
)


@pytest.mark.asyncio
<<<<<<< HEAD
async def test_console_logging_output(capsys):
=======
async def test_console_logging_output(capsys) -> None:
>>>>>>> pr-1962
    logger = RichConsoleLoggingResource(level=LogLevel.DEBUG)
=======

from entity.resources.logging import RichLoggingResource, LogLevel, LogCategory


@pytest.mark.asyncio
async def test_console_logging_output(capsys):
    logger = RichLoggingResource(level=LogLevel.DEBUG)
>>>>>>> pr-1961
    await logger.log(LogLevel.INFO, LogCategory.USER_ACTION, "hello", foo="bar")
    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "foo" in captured.out


@pytest.mark.asyncio
<<<<<<< HEAD
<<<<<<< HEAD
async def test_json_logging_output(capsys):
    pytest.skip("JSON logging requires file system access", allow_module_level=False)
    logger = RichJSONLoggingResource(level=LogLevel.DEBUG)
    await logger.log(LogLevel.WARNING, LogCategory.ERROR, "oops", code=123)
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())
    assert data["message"] == "oops"
    assert data["fields"]["code"] == 123
=======
async def test_json_logging_output(capsys) -> None:
    logger = RichJSONLoggingResource(level=LogLevel.DEBUG)
    await logger.log(LogLevel.WARNING, LogCategory.USER_ACTION, "oops", code=123)
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())
    assert data["message"] == "oops"
    assert data["fields"]["code"] == 123
>>>>>>> pr-1962
=======
async def test_json_logging_output(tmp_path):
    log_file = tmp_path / "log.json"
    logger = RichLoggingResource(
        level=LogLevel.DEBUG, json=True, log_file=str(log_file)
    )
    await logger.log(LogLevel.WARNING, LogCategory.ERROR, "oops", code=123)
    data = json.loads(log_file.read_text().splitlines()[0])
    assert data["message"] == "oops"
    assert data["fields"]["code"] == 123
>>>>>>> pr-1961
