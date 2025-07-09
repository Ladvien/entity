import asyncio
from pathlib import Path

from plugins.builtin.resources.local_filesystem import LocalFileSystemResource
from plugins.builtin.resources.storage_resource import StorageResource


async def make_resource(tmp_path: Path) -> StorageResource:
    fs = LocalFileSystemResource({"base_path": str(tmp_path)})
    res = StorageResource({})
    res.filesystem = fs
    return res


def test_store_and_load_file(tmp_path):
    async def run():
        storage = await make_resource(tmp_path)
        await storage.store_file("foo.txt", b"data")
        content = await storage.load_file("foo.txt")
        return content

    content = asyncio.run(run())
    assert content == b"data"
