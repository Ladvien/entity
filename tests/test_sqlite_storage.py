import asyncio
from datetime import datetime
from pathlib import Path

from pipeline.context import ConversationEntry
from plugins.builtin.resources.sqlite_storage import SQLiteStorageResource


async def history_roundtrip(tmp_path: Path) -> list[ConversationEntry]:
    cfg = {"path": tmp_path / "db.sqlite", "history_table": "history"}
    storage = SQLiteStorageResource(cfg)
    await storage.initialize()
    entry = ConversationEntry(content="hi", role="user", timestamp=datetime.now())
    await storage.save_history("conv1", [entry])
    rows = await storage.load_history("conv1")
    await storage.shutdown()
    return rows


def test_history_roundtrip(tmp_path):
    history = asyncio.run(history_roundtrip(tmp_path))
    assert history and history[0].content == "hi"


async def run_health_check(tmp_path: Path) -> bool:
    cfg = {"path": tmp_path / "hc.sqlite"}
    storage = SQLiteStorageResource(cfg)
    await storage.initialize()
    result = await storage.health_check()
    await storage.shutdown()
    return result


def test_health_check(tmp_path):
    assert asyncio.run(run_health_check(tmp_path))
