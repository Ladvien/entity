import subprocess
import sys

import yaml


def test_config_validator_success(tmp_path):
    config = {"plugins": {"resources": {"a": {"type": "tests.test_initializer:A"}}}}
    path = tmp_path / "valid.yml"
    path.write_text(yaml.dump(config, sort_keys=False))

    result = subprocess.run(
        [sys.executable, "-m", "src.entity_config.validator", "--config", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Configuration valid" in result.stdout


def test_config_validator_failure(tmp_path):
    config = {"plugins": {"prompts": {"d": {"type": "tests.test_initializer:D"}}}}
    path = tmp_path / "bad.yml"
    path.write_text(yaml.dump(config, sort_keys=False))

    result = subprocess.run(
        [sys.executable, "-m", "src.entity_config.validator", "--config", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "missing dependency" in result.stdout.lower()


def test_config_validator_schema_error(tmp_path):
    config = {"server": {"host": "localhost", "port": "not-int"}}
    path = tmp_path / "schema.yml"
    path.write_text(yaml.dump(config, sort_keys=False))

    result = subprocess.run(
        [sys.executable, "-m", "src.entity_config.validator", "--config", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "port" in result.stdout.lower()
