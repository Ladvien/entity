import os

import pytest

from entity.config import VariableResolver


def test_env_file_substitution(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("BASE=http://example.com\nURL=${BASE}/api\n")
    resolver = VariableResolver(str(env_file))
    result = resolver.substitute({"endpoint": "${URL}"})
    assert result["endpoint"] == "http://example.com/api"


def test_missing_variable():
    resolver = VariableResolver()
    with pytest.raises(ValueError, match="not found"):
        resolver.substitute({"a": "${UNKNOWN}"})


def test_cycle_detection(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("A=${B}\nB=${A}\n")
    resolver = VariableResolver(str(env_file))
    with pytest.raises(ValueError, match="Circular reference"):
        resolver.substitute("${A}")


def test_auto_env_loading(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("VAR=value")
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = VariableResolver.substitute_variables("${VAR}")
        assert result == "value"
    finally:
        os.chdir(cwd)
