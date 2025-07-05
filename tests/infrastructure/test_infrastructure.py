import subprocess
from unittest import mock

import pytest

# skip tests if infrastructure module is missing
infrastructure = pytest.importorskip("plugins.builtin.infrastructure")
Infrastructure = infrastructure.Infrastructure


@pytest.fixture()
def sample_config():
    return {
        "terraform": {
            "variables": {"region": "${AWS_REGION}"},
            "working_dir": "./terraform",
        }
    }


def test_env_variable_interpolation(monkeypatch, sample_config):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    infra = Infrastructure(sample_config)
    assert infra.config["terraform"]["variables"]["region"] == "us-east-1"


@mock.patch("subprocess.run")
def test_terraform_plan_generation(run_mock, sample_config):
    run_mock.return_value = subprocess.CompletedProcess(
        ["terraform", "plan"], returncode=0
    )
    infra = Infrastructure(sample_config)
    infra.plan()
    run_mock.assert_called()
