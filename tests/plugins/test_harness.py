from __future__ import annotations

from pathlib import Path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("src").resolve()))

from tests.plugins.harness import run_plugin


def test_run_plugin(tmp_path: Path) -> None:
    plugin_file = tmp_path / "plug.py"
    plugin_file.write_text(
        "from entity.core.plugins import ToolPlugin\n"
        "from entity.core.stages import PipelineStage\n\n"
        "class Demo(ToolPlugin):\n"
        "    stages = [PipelineStage.DO]\n"
        "    async def execute_function(self, params):\n"
        "        return params\n"
    )
    run_plugin(str(plugin_file))
