import json
from pathlib import Path

import pytest

from entity.resources.logging import (
    ConsoleLoggingResource,
    JSONLoggingResource,
    LogCategory,
    LogContext,
    LogLevel,
)


@pytest.mark.asyncio
async def test_console_logging(capsys):
    logger = ConsoleLoggingResource(level=LogLevel.DEBUG)
    ctx = LogContext(user_id="u1")
    await logger.log(LogLevel.INFO, LogCategory.USER_ACTION, "hello", ctx)
    captured = capsys.readouterr().out
    assert "hello" in captured
    assert logger.records[0]["level"] == LogLevel.INFO.value


@pytest.mark.asyncio
async def test_json_logging(tmp_path: Path):
    log_file = tmp_path / "log.json"
    logger = JSONLoggingResource(level=LogLevel.INFO, output_file=str(log_file))
    ctx = LogContext(user_id="u2")
    await logger.log(LogLevel.INFO, LogCategory.USER_ACTION, "hi", ctx)
    data = json.loads(log_file.read_text())
    assert data["message"] == "hi"
    assert logger.records[0]["message"] == "hi"


@pytest.mark.asyncio
async def test_json_log_rotation(tmp_path: Path):
    log_file = tmp_path / "log.json"
    logger = JSONLoggingResource(
        level=LogLevel.INFO,
        output_file=str(log_file),
        max_bytes=10,
        backup_count=1,
    )
    ctx = LogContext(user_id="u3")
    for _ in range(5):
        await logger.log(LogLevel.INFO, LogCategory.USER_ACTION, "x" * 5, ctx)
    backups = list(log_file.parent.glob("log.json.*"))
    assert backups
