import asyncio
from datetime import datetime
from pathlib import Path

from experiments.storage import StorageResource
from pipeline.context import ConversationEntry
from plugins.builtin.resources.in_memory_storage import InMemoryStorageResource
from plugins.builtin.resources.local_filesystem import LocalFileSystemResource


async def make_storage(tmp_path: Path) -> StorageResource:
    fs = LocalFileSystemResource({"base_path": str(tmp_path)})
    db = InMemoryStorageResource({})
    storage = StorageResource(database=db, filesystem=fs)
    await storage.initialize()
    return storage


def test_store_and_load_file(tmp_path: Path) -> None:
    async def run() -> bytes:
        storage = await make_storage(tmp_path)
        await storage.store_file("foo.txt", b"bar")
        content = await storage.load_file("foo.txt")
        await storage.shutdown()
        return content

    assert asyncio.run(run()) == b"bar"


def test_save_and_load_history(tmp_path: Path) -> None:
    async def run() -> list[ConversationEntry]:
        storage = await make_storage(tmp_path)
        entry = ConversationEntry(
            content="hi", role="user", timestamp=datetime.now(), metadata={}
        )
        await storage.save_conversation("1", [entry])
        history = await storage.load_conversation("1")
        await storage.shutdown()
        return history

    history = asyncio.run(run())
    assert history and history[0].content == "hi"
