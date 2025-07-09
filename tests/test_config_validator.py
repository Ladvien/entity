import yaml
from pipeline.config import ConfigLoader
from entity.config.models import EntityConfig


def test_config_validator_success(tmp_path):
    config = {"plugins": {"resources": {"a": {"type": "tests.test_initializer:A"}}}}
    path = tmp_path / "valid.yml"
    path.write_text(yaml.dump(config))

    EntityConfig.from_dict(ConfigLoader.from_yaml(path))


def test_config_validator_failure(tmp_path):
    config = {"plugins": {"prompts": {"d": {"type": "tests.test_initializer:D"}}}}
    path = tmp_path / "bad.yml"
    path.write_text(yaml.dump(config))

    try:
        EntityConfig.from_dict(ConfigLoader.from_yaml(path))
    except Exception as exc:
        assert "missing dependency" in str(exc).lower()
    else:
        raise AssertionError("validation should fail")


def test_config_validator_schema_error(tmp_path):
    config = {"server": {"host": "localhost", "port": "not-int"}}
    path = tmp_path / "schema.yml"
    path.write_text(yaml.dump(config))

    try:
        EntityConfig.from_dict(ConfigLoader.from_yaml(path))
    except Exception as exc:
        assert "port" in str(exc).lower()
    else:
        raise AssertionError("validation should fail")
