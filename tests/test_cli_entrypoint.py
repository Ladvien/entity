import subprocess
import sys

import yaml


def test_cli_entrypoint(tmp_path):
    config = {"server": {"host": "127.0.0.1", "port": 8123}}
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config, sort_keys=False))

    result = subprocess.run(
        [sys.executable, "src/cli.py", "--config", str(path), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "usage" in result.stdout.lower()
