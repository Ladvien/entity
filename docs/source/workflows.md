# Example Workflows

Entity provides a few ready-to-use workflow classes. Each workflow maps pipeline
stages to plugin names. Workflows act as blueprints; supply your own plugin
names when instantiating them and reuse the class across environments.

```python
from entity.workflows.examples import ChainOfThoughtWorkflow
from pipeline import Pipeline

workflow = ChainOfThoughtWorkflow(
    prompt="user_plugins.prompts.chain_of_thought:ChainOfThoughtPrompt"
)
pipeline = Pipeline(workflow=workflow)
```

## Available Workflows

### ChainOfThoughtWorkflow
Runs the chain-of-thought reasoning plugin.

```python
from entity.workflows.examples import ChainOfThoughtWorkflow
workflow = ChainOfThoughtWorkflow(
    prompt="user_plugins.prompts.chain_of_thought:ChainOfThoughtPrompt"
)
```

### ReActWorkflow
Uses the ReAct prompt to alternate reasoning and tool use.

```python
from entity.workflows.examples import ReActWorkflow
workflow = ReActWorkflow(prompt="user_plugins.prompts.react_prompt:ReActPrompt")
```

### IntentClassificationWorkflow
Classifies user intent with a single LLM call.

```python
from entity.workflows.examples import IntentClassificationWorkflow
workflow = IntentClassificationWorkflow(
    prompt="user_plugins.prompts.intent_classifier:IntentClassifierPrompt"
)
```
