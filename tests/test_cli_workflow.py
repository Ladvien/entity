import pathlib
import sys
from typing import Iterable

import pytest

from entity.workflows.base import Workflow
from entity.pipeline.stages import PipelineStage

sys.path.insert(0, str(pathlib.Path("src").resolve()))

from entity.cli import EntityCLI, CLIArgs


class DummyCLI(EntityCLI):
    def _parse_args(self) -> CLIArgs:  # type: ignore[override]
        return CLIArgs(None, None, command="")


def _make_cli() -> DummyCLI:
    return DummyCLI()


def test_load_workflow_yaml(tmp_path):
    yaml_path = tmp_path / "wf.yaml"
    yaml_path.write_text(
        "workflow:\n  INPUT: ['one']\n  OUTPUT: ['two']\n",
        encoding="utf-8",
    )
    cli = _make_cli()
    workflow = cli._load_workflow(str(yaml_path))
    assert workflow == {"INPUT": ["one"], "OUTPUT": ["two"]}


def test_visualize_workflow_yaml(tmp_path, capsys):
    yaml_path = tmp_path / "wf.yaml"
    yaml_path.write_text(
        "workflow:\n  INPUT: ['one']\n  OUTPUT: ['two']\n",
        encoding="utf-8",
    )
    cli = _make_cli()
    cli._workflow_visualize(str(yaml_path), fmt="ascii")
    captured = capsys.readouterr().out.strip()
    assert "INPUT" in captured and "-> one" in captured


class VisualCLI(EntityCLI):
    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        super().__init__()

    def _parse_args(self) -> CLIArgs:  # type: ignore[override]
        return CLIArgs(
            None,
            None,
            command="workflow",
            workflow_cmd="visualize",
            file=self._file_path,
            fmt="ascii",
        )


def test_cli_visualize_command(tmp_path, capsys):
    yaml_path = tmp_path / "wf.yaml"
    yaml_path.write_text(
        "workflow:\n  INPUT: ['one']\n  OUTPUT: ['two']\n",
        encoding="utf-8",
    )
    cli = VisualCLI(str(yaml_path))
    cli.run()
    captured = capsys.readouterr().out.strip()
    assert "INPUT" in captured and "-> one" in captured


class _Registry:
    def __init__(self, names: Iterable[str]):
        self._names = set(names)

    def has_plugin(self, name: str) -> bool:
        return name in self._names

    def list_plugins(self) -> list[str]:
        return sorted(self._names)


def test_workflow_validation():
    registry = _Registry(["Known"])
    with pytest.raises(KeyError):
        Workflow({PipelineStage.INPUT: ["Known", "Missing"]}, registry=registry)


def test_parent_inheritance():
    class BaseWF(Workflow):
        stage_map = {PipelineStage.INPUT: ["one"]}

    class ChildWF(Workflow):
        parent = BaseWF
        stage_map = {PipelineStage.OUTPUT: ["two"]}

    wf = ChildWF()
    assert PipelineStage.INPUT in wf.stages
    assert PipelineStage.OUTPUT in wf.stages
