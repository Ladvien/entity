from entity.workflows.discovery import discover_workflows
from entity.workflows import Workflow


def test_discover_workflows(tmp_path):
    wf_file = tmp_path / "wf.py"
    wf_file.write_text(
        """
from entity.workflows import Workflow
class MyFlow(Workflow):
    pass
"""
    )
    workflows = discover_workflows(str(tmp_path))
    assert "MyFlow" in workflows
    assert issubclass(workflows["MyFlow"], Workflow)


def test_discover_multiple_files(tmp_path):
    (tmp_path / "a.py").write_text(
        "from entity.workflows import Workflow\nclass A(Workflow):\n    pass"
    )
    (tmp_path / "b.py").write_text(
        "class IgnoreMe: pass\nfrom entity.workflows import Workflow\nclass B(Workflow):\n    pass"
    )
    workflows = discover_workflows(str(tmp_path))
    assert set(workflows) == {"A", "B"}


def test_discover_ignores_import_errors(tmp_path):
    (tmp_path / "broken.py").write_text("raise Exception('boom')")
    workflows = discover_workflows(str(tmp_path))
    assert workflows == {}
