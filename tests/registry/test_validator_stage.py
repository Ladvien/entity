import pytest
import yaml

from pipeline import PipelineStage, PromptPlugin
from registry.validator import RegistryValidator


class GoodPlugin(PromptPlugin):
    stages = [PipelineStage.THINK]

    async def _execute_impl(self, context):
        return None


class BadPlugin(PromptPlugin):
    stages = ["BROKEN_STAGE"]
    skip_stage_validation = True

    async def _execute_impl(self, context):
        return None


def test_validator_rejects_invalid_stage(tmp_path):
    config = {
        "plugins": {
            "prompts": {
                "bad": {"type": "tests.registry.test_validator_stage:BadPlugin"}
            }
        }
    }
    path = tmp_path / "invalid.yml"
    path.write_text(yaml.dump(config, sort_keys=False))

    validator = RegistryValidator(str(path))
    with pytest.raises(SystemError, match="invalid stage values"):
        validator.run()


def test_validator_accepts_valid_stage(tmp_path):
    config = {
        "plugins": {
            "prompts": {
                "good": {"type": "tests.registry.test_validator_stage:GoodPlugin"}
            }
        }
    }
    path = tmp_path / "valid.yml"
    path.write_text(yaml.dump(config, sort_keys=False))

    validator = RegistryValidator(str(path))
    validator.run()
