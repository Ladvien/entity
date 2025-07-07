import subprocess
import sys


def test_analyze_plugin(tmp_path):
    path = tmp_path / "my_plugin.py"
    path.write_text(
        """async def my_plugin(ctx):\n    # analyze input\n    await ctx.ask_llm('hi')\n"""
    )
    result = subprocess.run(
        [sys.executable, "src/cli/plugin_tool.py", "analyze-plugin", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "my_plugin -> think" in result.stdout.lower()


def test_analyze_plugin_failure(tmp_path):
    path = tmp_path / "bad.py"
    path.write_text("def no_plugin():\n    pass\n")
    result = subprocess.run(
        [sys.executable, "src/cli/plugin_tool.py", "analyze-plugin", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
