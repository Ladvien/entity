import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not installed")
def test_template_loading_in_docker(tmp_path):
    script = "\n".join(
        [
            "import sys",
            "sys.path.insert(0, '/src/src')",
            "from entity.workflow.templates import load_template",
            (
                "wf = load_template('basic',"
                " think_plugin='entity.plugins.defaults.ThinkPlugin',"
                " output_plugin='entity.plugins.defaults.OutputPlugin')"
            ),
            "print(wf.plugins_for('think')[0].__name__)",
        ]
    )
    script_file = tmp_path / "run.py"
    script_file.write_text(script)

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
            "pip install /src >/tmp/pip.log && python /data/run.py",
        ],
        text=True,
    ).strip()

    assert result == "ThinkPlugin"
