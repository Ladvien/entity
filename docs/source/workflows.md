# Workflows

A `Workflow` maps pipeline stages to plugin names. When instantiated it can now
accept a `conditions` dictionary for dynamically skipping stages.
Each key is a `PipelineStage` and the value is a callable receiving the current
`PipelineState`. If the callable returns `False` the stage is skipped.

```python
from entity.pipeline.stages import PipelineStage
from entity.workflows.base import Workflow

class MyWorkflow(Workflow):
    stage_map = {PipelineStage.THINK: ["MyPlugin"]}

wf = MyWorkflow(conditions={PipelineStage.THINK: lambda state: state.iteration == 1})
```

`should_execute()` evaluates these conditions before running each stage.

