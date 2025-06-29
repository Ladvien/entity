import subprocess
import sys

import yaml

from pipeline import PipelineStage, PromptPlugin, ValidationResult


class ReloadPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]
    name = "reload"

    async def _execute_impl(self, context):
        pass

    @classmethod
    def validate_config(cls, config):
        if "value" not in config:
            return ValidationResult.error_result("missing value")
        return ValidationResult.success_result()


def _write_config(path, value=True):
    cfg = {
        "plugins": {
            "prompts": {
                "reload": {
                    "type": "tests.test_cli_reload:ReloadPlugin",
                }
            }
        }
    }
    if value is not False:
        cfg["plugins"]["prompts"]["reload"]["value"] = value
    path.write_text(yaml.dump(cfg))


def test_cli_reload_success(tmp_path):
    base = tmp_path / "base.yml"
    update = tmp_path / "update.yml"
    _write_config(base, value="one")
    _write_config(update, value="two")

    result = subprocess.run(
        [
            sys.executable,
            "src/cli.py",
            "--config",
            str(base),
            "reload-config",
            str(update),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert "Updated reload" in result.stdout


def test_cli_reload_failure(tmp_path):
    base = tmp_path / "base.yml"
    bad = tmp_path / "bad.yml"
    _write_config(base, value="one")
    _write_config(bad, value=False)

    result = subprocess.run(
        [
            sys.executable,
            "src/cli.py",
            "--config",
            str(base),
            "reload-config",
            str(bad),
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "Failed to update" in result.stdout
