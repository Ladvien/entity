import json
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not installed")
def test_nested_substitution_in_docker(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("BASE=http://service\nURL=${BASE}/api\n")

    script = "\n".join(
        [
            "import sys, json",
            "sys.path.insert(0, '/src/src')",
            "from entity.config import VariableResolver",
            "resolver = VariableResolver('/data/.env')",
            "print(json.dumps(resolver.substitute({'endpoint': '${URL}'})))",
        ]
    )

    result = subprocess.check_output(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{Path.cwd()}:/src",
            "-v",
            f"{tmp_path}:/data",
            "python:3.11-slim",
            "python",
            "-c",
            script,
        ],
        text=True,
    ).strip()

    assert json.loads(result)["endpoint"] == "http://service/api"
