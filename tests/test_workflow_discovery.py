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
