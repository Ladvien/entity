import asyncio
from pipeline.initializer import SystemInitializer
from entity.workflows import Workflow


def test_initializer_discovers_workflows(tmp_path):
    f = tmp_path / "wf.py"
    f.write_text(
        """
from entity.workflows import Workflow
class InitFlow(Workflow):
    pass
"""
    )
    config = {"workflow_dirs": [str(tmp_path)], "plugins": {}}
    initializer = SystemInitializer.from_dict(config)
    asyncio.run(initializer.initialize())
    assert "InitFlow" in initializer.workflows
    assert issubclass(initializer.workflows["InitFlow"], Workflow)
