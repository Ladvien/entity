import os

from entity_config.environment import load_env


def test_load_env_falls_back_to_example(tmp_path, monkeypatch):
    example = tmp_path / ".env.example"
    example.write_text("FOO=bar\nBAZ=qux")
    env_path = tmp_path / ".env"

    monkeypatch.delenv("FOO", raising=False)
    monkeypatch.delenv("BAZ", raising=False)

    load_env(env_path)

    assert os.environ.get("FOO") == "bar"
    assert os.environ.get("BAZ") == "qux"
