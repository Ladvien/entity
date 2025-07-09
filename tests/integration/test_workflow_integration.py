import asyncio
import pytest

pipeline = pytest.importorskip("pipeline")
workflow_mod = pytest.importorskip("entity.workflows.react")

Pipeline = getattr(pipeline, "Pipeline", None)
ReActWorkflow = getattr(workflow_mod, "ReActWorkflow", None)

if Pipeline is None or ReActWorkflow is None:
    pytest.skip("Workflow APIs not available", allow_module_level=True)


@pytest.mark.integration
def test_react_workflow_pipeline_runs():
    runtime = Pipeline(approach=ReActWorkflow())
    result = asyncio.run(runtime.run_pipeline("hi"))
    assert result
