import os
import subprocess
import sys
from textwrap import dedent

import yaml


PLUGIN_MODULE = """
from pipeline.stages import PipelineStage
from entity.core.plugins import PromptPlugin, ToolPlugin, ValidationResult
from entity.core.context import PluginContext


class ReloadPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]
    name = "reload"

    async def _execute_impl(self, context: PluginContext) -> None:
        return None

    @classmethod
    def validate_config(cls, config: dict) -> ValidationResult:
        if "value" not in config:
            return ValidationResult.error_result("missing value")
        return ValidationResult.success_result()


class ReloadTool(ToolPlugin):
    name = "echo"

    async def execute_function(self, params: dict) -> str:
        return str(params.get("text", ""))
"""


def _module_path(tmp_path):
    module = tmp_path / "reload_module.py"
    module.write_text(dedent(PLUGIN_MODULE))
    return module


def _write_config(path, module_name, value=True, tool=False, include_plugin=True):
    cfg = {"plugins": {"prompts": {}}}
    if include_plugin:
        cfg["plugins"]["prompts"]["reload"] = {"type": f"{module_name}:ReloadPlugin"}
    if include_plugin and value is not False:
        cfg["plugins"]["prompts"]["reload"]["value"] = value
    if tool:
        cfg["plugins"].setdefault("tools", {})["echo"] = {
            "type": f"{module_name}:ReloadTool"
        }
    path.write_text(yaml.dump(cfg, sort_keys=False))


def _run_cli(base: str, update: str, env: dict) -> subprocess.CompletedProcess[str]:
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


def test_cli_reload_success(tmp_path):
    module = _module_path(tmp_path)
    base = tmp_path / "base.yml"
    update = tmp_path / "update.yml"
    _write_config(base, module.stem, value="one")
    _write_config(update, module.stem, value="two")

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}:{env.get('PYTHONPATH','')}"
    result = _run_cli(str(base), str(update), env)
    assert result.returncode == 0


def test_cli_reload_failure(tmp_path):
    module = _module_path(tmp_path)
    base = tmp_path / "base.yml"
    bad = tmp_path / "bad.yml"
    _write_config(base, module.stem, value="one")
    _write_config(bad, module.stem, value=False)

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}:{env.get('PYTHONPATH','')}"
    result = _run_cli(str(base), str(bad), env)
    assert result.returncode != 0
    assert "Failed to update" in result.stderr


def test_cli_reload_add_tool(tmp_path):
    module = _module_path(tmp_path)
    base = tmp_path / "base.yml"
    update = tmp_path / "update.yml"
    _write_config(base, module.stem, value="one")
    _write_config(update, module.stem, value="two", tool=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}:{env.get('PYTHONPATH','')}"
    result = _run_cli(str(base), str(update), env)
    assert result.returncode != 0


def test_cli_reload_remove_plugin(tmp_path):
    module = _module_path(tmp_path)
    base = tmp_path / "base.yml"
    update = tmp_path / "update.yml"
    _write_config(base, module.stem, value="one")
    _write_config(update, module.stem, include_plugin=False)

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}:{env.get('PYTHONPATH','')}"
    result = _run_cli(str(base), str(update), env)
    assert result.returncode != 0
