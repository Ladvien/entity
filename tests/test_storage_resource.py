import asyncio
from datetime import datetime
from pathlib import Path

from plugins.builtin.resources.in_memory_storage import InMemoryStorageResource
from plugins.builtin.resources.local_filesystem import LocalFileSystemResource

from pipeline.context import ConversationEntry
from pipeline.resources.storage_resource import StorageResource


async def make_resource(tmp_path: Path) -> StorageResource:
    db = InMemoryStorageResource({})
    fs = LocalFileSystemResource({"base_path": str(tmp_path)})
    res = StorageResource(database=db, filesystem=fs)
    return res


def test_save_and_load_history(tmp_path):
    async def run():
        storage = await make_resource(tmp_path)
        history = [
            ConversationEntry(content="hi", role="user", timestamp=datetime.now())
        ]
        await storage.save_history("1", history)
        loaded = await storage.load_history("1")
        return loaded

    loaded = asyncio.run(run())
    assert loaded and loaded[0].content == "hi"


def test_store_and_load_file(tmp_path):
    async def run():
        storage = await make_resource(tmp_path)
        await storage.store_file("foo.txt", b"data")
        content = await storage.load_file("foo.txt")
        return content

    content = asyncio.run(run())
    assert content == b"data"
