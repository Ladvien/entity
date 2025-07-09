import subprocess
import sys


def test_scaffold_plugin(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.tools.plugin_cli",
            "example_plugin",
            "--type",
            "prompt",
            "--out",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    path = tmp_path / "example_plugin.py"
    assert path.exists()
    content = path.read_text()
    assert "class ExamplePlugin" in content


def test_scaffold_invalid_type(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.tools.plugin_cli",
            "bad_plugin",
            "--type",
            "unknown",
            "--out",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not (tmp_path / "bad_plugin.py").exists()
