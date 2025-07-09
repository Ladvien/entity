from pathlib import Path

from pipeline.reliability.queue import PersistentQueue


def test_persistent_queue(tmp_path: Path):
    q = PersistentQueue(str(tmp_path / "q.json"))
    q.put({"a": 1})
    assert len(q) == 1
    item = q.get()
    assert item == {"a": 1}
