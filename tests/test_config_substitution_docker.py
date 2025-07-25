import json
import shutil
import subprocess
import sys
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
    script_file = tmp_path / "run.py"
    script_file.write_text(script)

    wheel_dir = tmp_path / "wheel"
    wheel_dir.mkdir()
    subprocess.check_call(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(wheel_dir)]
    )
    wheel_path = next(wheel_dir.glob("*.whl"))

    result = subprocess.check_output(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{Path.cwd()}:/src",
            "-v",
            f"{tmp_path}:/data",
            "-w",
            "/src",
            "python:3.11-slim",
            "sh",
            "-c",
            (
                f"pip install /data/wheel/{wheel_path.name} --no-deps >/tmp/pip.log"
                " && python /data/run.py"
            ),
        ],
        text=True,
    ).strip()

    assert json.loads(result)["endpoint"] == "http://service/api"
