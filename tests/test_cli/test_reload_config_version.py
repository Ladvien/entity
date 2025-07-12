import os
import subprocess
import sys
from textwrap import dedent

import yaml


PLUGIN_MODULE = """
from pathlib import Path
from pipeline.stages import PipelineStage
from entity.core.plugins import PromptPlugin


class RecorderPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]
    name = "recorder"

    def __init__(self, config):
        super().__init__(config)
        self.output = config["output"]

    async def _execute_impl(self, context):
        return None

    async def _handle_reconfiguration(self, old, new):
        Path(self.output).write_text(f"{new['value']};{self.config_version + 1}")
"""


def _module_path(tmp_path):
    module = tmp_path / "recorder.py"
    module.write_text(dedent(PLUGIN_MODULE))
    return module


def _write_config(path, module_name, value, output, **extra):
    cfg = {
        "plugins": {
            "prompts": {
                "recorder": {
                    "type": f"{module_name}:RecorderPlugin",
                    "value": value,
                    "output": str(output),
                }
            }
        }
    }
    cfg["plugins"]["prompts"]["recorder"].update(extra)
    path.write_text(yaml.dump(cfg, sort_keys=False))


def _run_cli(base, update, env):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "entity.cli",
            "--config",
            base,
            "reload-config",
            update,
        ],
        text=True,
        capture_output=True,
        env=env,
    )


def test_reload_updates_config_version(tmp_path):
    module = _module_path(tmp_path)
    result_file = tmp_path / "out.txt"
    base = tmp_path / "base.yml"
    update = tmp_path / "update.yml"
    _write_config(base, module.stem, "one", result_file)
    _write_config(update, module.stem, "two", result_file)

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}:{env.get('PYTHONPATH','')}"
    result = _run_cli(str(base), str(update), env)
    assert result.returncode == 0
    value, version = result_file.read_text().split(";")
    assert value == "two"
    assert version == "2"


def test_reload_stage_change_requires_restart(tmp_path):
    module = _module_path(tmp_path)
    result_file = tmp_path / "out.txt"
    base = tmp_path / "base.yml"
    update = tmp_path / "update.yml"
    _write_config(base, module.stem, "one", result_file)
    _write_config(update, module.stem, "two", result_file, stages=["DO"])

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}:{env.get('PYTHONPATH','')}"
    result = _run_cli(str(base), str(update), env)
    assert result.returncode == 2
    assert "Topology changes require restart" in result.stderr


def test_reload_dependency_change_requires_restart(tmp_path):
    module = _module_path(tmp_path)
    result_file = tmp_path / "out.txt"
    base = tmp_path / "base.yml"
    update = tmp_path / "update.yml"
    _write_config(base, module.stem, "one", result_file)
    _write_config(update, module.stem, "two", result_file, dependencies=["x"])

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}:{env.get('PYTHONPATH','')}"
    result = _run_cli(str(base), str(update), env)
    assert result.returncode == 2
    assert "Topology changes require restart" in result.stderr
