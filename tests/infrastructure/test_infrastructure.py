import shutil
import subprocess

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


def test_terraform_plan_generation(sample_config):
    if shutil.which("terraform") is None:
        pytest.skip("Terraform not installed")
    infra = Infrastructure(sample_config)
    proc = subprocess.run(
        ["terraform", "version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if proc.returncode != 0:
        pytest.skip("Terraform CLI not available")
    infra.plan()
