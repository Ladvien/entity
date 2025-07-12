import os
import subprocess
import sys
import yaml
from textwrap import dedent


def test_cli_validate_success(tmp_path):
    cfg_path = tmp_path / "cfg.yml"
    plugin_module = tmp_path / "ok.py"
    plugin_module.write_text(
        dedent(
            """
            from pipeline.stages import PipelineStage
            from entity.core.plugins import PromptPlugin


            class OkPlugin(PromptPlugin):
                stages = [PipelineStage.THINK]

                @classmethod
                def validate_dependencies(cls, registry):
                    from entity.core.plugins import ValidationResult

                    return ValidationResult.success_result()

                @classmethod
                def validate_config(cls, cfg):
                    from entity.core.plugins import ValidationResult

                    return ValidationResult.success_result()

                async def _execute_impl(self, context):
                    pass
            """
        )
    )
    cfg = {
        "workflow": {"think": ["ok"]},
        "plugins": {"prompts": {"ok": {"type": f"{plugin_module.stem}:OkPlugin"}}},
    }
    cfg_path.write_text(yaml.dump(cfg, sort_keys=False))
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}:{env.get('PYTHONPATH', '')}"
    result = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--config", str(cfg_path), "validate"],
        text=True,
        capture_output=True,
        env=env,
    )
    assert result.returncode == 0


def test_cli_validate_failure(tmp_path):
    plugin_module = tmp_path / "bad.py"
    plugin_module.write_text(
        dedent(
            """
            from pipeline.stages import PipelineStage
            from entity.core.plugins import PromptPlugin


            class BadPlugin(PromptPlugin):
                stages = [PipelineStage.THINK]
                dependencies = ["missing"]

                async def _execute_impl(self, context):
                    pass
            """
        )
    )

    cfg = {"plugins": {"prompts": {"bad": {"type": f"{plugin_module.stem}:BadPlugin"}}}}
    cfg_path = tmp_path / "bad.yml"
    cfg_path.write_text(yaml.dump(cfg, sort_keys=False))

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{tmp_path}:{env.get('PYTHONPATH', '')}"

    result = subprocess.run(
        [sys.executable, "-m", "entity.cli", "--config", str(cfg_path), "validate"],
        text=True,
        capture_output=True,
        env=env,
    )
    assert result.returncode != 0
