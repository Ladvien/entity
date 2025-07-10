import subprocess
import sys
import yaml


def test_create_agent(tmp_path):
    dest = tmp_path / "agent"
    result = subprocess.run(
        [sys.executable, "-m", "entity.cli", "create-agent", str(dest)],
        text=True,
        capture_output=True,
        check=True,
    )
    assert (dest / "src" / "main.py").exists()
    config_path = dest / "config" / "dev.yaml"
    assert config_path.exists()
    cfg = yaml.safe_load(config_path.read_text())
    assert cfg["server"]["port"] == 8000
