import shutil
from pathlib import Path

import pytest


@pytest.fixture()
def local_duckdb_path(tmp_path: Path) -> Path:
    path = tmp_path / "db.duckdb"
    yield path
    if path.exists():
        path.unlink()


@pytest.fixture()
def local_storage_dir(tmp_path: Path) -> Path:
    path = tmp_path / "storage"
    path.mkdir()
    yield path
    shutil.rmtree(path, ignore_errors=True)
