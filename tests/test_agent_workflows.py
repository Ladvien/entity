from entity import Agent
from entity.workflows import Workflow


def test_agent_load_workflows(tmp_path):
    path = tmp_path / "flows.py"
    path.write_text(
        """
from entity.workflows import Workflow
class Demo(Workflow):
    pass
"""
    )
    agent = Agent()
    agent.load_workflows_from_directory(str(tmp_path))
    assert "Demo" in agent.workflows
    assert issubclass(agent.workflows["Demo"], Workflow)
