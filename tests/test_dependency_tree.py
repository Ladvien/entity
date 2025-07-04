import subprocess
import sys


def test_no_circular_dependencies() -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pipdeptree"])
    result = subprocess.run(
        [sys.executable, "-m", "pipdeptree", "--warn", "fail"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
