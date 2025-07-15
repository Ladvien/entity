import os
from entity.config.environment import load_env


def test_env_file_loading(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=env\n")
    prev = os.getcwd()
    os.chdir(tmp_path)
    os.environ.pop("FOO", None)

    load_env(env_file)

    assert os.environ["FOO"] == "env"
    os.chdir(prev)


def test_env_does_not_override_existing(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("BAR=env\n")
    prev = os.getcwd()
    os.chdir(tmp_path)
    os.environ["BAR"] = "os"

    load_env(env_file)

    assert os.environ["BAR"] == "os"
    os.chdir(prev)


def test_secret_overrides_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("BAZ=env\n")
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    secret_file = secrets / "dev.env"
    secret_file.write_text("BAZ=secret\n")
    prev = os.getcwd()
    os.chdir(tmp_path)
    os.environ.pop("BAZ", None)

    load_env(env_file, env="dev")

    assert os.environ["BAZ"] == "secret"
    os.chdir(prev)


def test_os_env_overrides_secret(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("QUX=env\n")
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    secret_file = secrets / "prod.env"
    secret_file.write_text("QUX=secret\n")
    prev = os.getcwd()
    os.chdir(tmp_path)
    os.environ["QUX"] = "os"

    load_env(env_file, env="prod")

    assert os.environ["QUX"] == "os"
    os.chdir(prev)
