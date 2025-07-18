import os
from entity.defaults import ensure_defaults, ollama_available, _reset_defaults
from entity.core.agent import Agent


def test_ensure_defaults_creates_duckdb(tmp_path):
    db = tmp_path / "db.duckdb"
    files = tmp_path / "files"
    _reset_defaults()
    ensure_defaults(db_path=str(db), files_dir=str(files))
    assert db.exists()
    assert files.exists()


def test_agent_auto_defaults(tmp_path):
    prev = os.getcwd()
    os.chdir(tmp_path)
    _reset_defaults()
    Agent()
    assert (tmp_path / "agent_memory.duckdb").exists()
    os.chdir(prev)


def test_ollama_available_returns_bool():
    assert isinstance(ollama_available(), bool)
