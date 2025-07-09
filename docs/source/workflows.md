# Example Workflows

Entity provides a few ready-to-use workflow classes. Each workflow maps pipeline
stages to plugin names. Instantiate one and pass it to `Pipeline`.

```python
from entity.workflows.examples import ChainOfThoughtWorkflow
from pipeline import Pipeline

workflow = ChainOfThoughtWorkflow()
pipeline = Pipeline(workflow=workflow)
```

## Available Workflows

### ChainOfThoughtWorkflow
Runs the chain-of-thought reasoning plugin.

```python
from entity.workflows.examples import ChainOfThoughtWorkflow
```

### ReActWorkflow
Uses the ReAct prompt to alternate reasoning and tool use.

```python
from entity.workflows.examples import ReActWorkflow
```

### IntentClassificationWorkflow
Classifies user intent with a single LLM call.

```python
from entity.workflows.examples import IntentClassificationWorkflow
```
