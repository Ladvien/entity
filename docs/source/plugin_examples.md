# Plugin Examples

The `examples/plugins/` directory contains minimal plugins for each pipeline stage.
These demonstrate how to interact with the `PluginContext` and which methods
are appropriate for different stages.

## InputLogger

`InputLogger` runs during the **INPUT** stage and saves the raw user message for
later steps.

```python
from examples.plugins.input_logger import InputLogger
```

```python
class InputLogger(InputAdapterPlugin):
    stages = [PipelineStage.INPUT]

    async def _execute_impl(self, context: PluginContext) -> None:
        message = context.conversation()[-1].content if context.conversation() else ""
        await context.think("raw_input", message)
```

## MessageParser

`MessageParser` executes in the **PARSE** stage and normalizes the user's
message.

```python
class MessageParser(PromptPlugin):
    stages = [PipelineStage.PARSE]

    async def _execute_impl(self, context: PluginContext) -> None:
        raw = context.conversation()[-1].content if context.conversation() else ""
        await context.think("parsed_input", raw.strip().lower())
```

## ResponseReviewer

`ResponseReviewer` runs in the **REVIEW** stage to modify the final response if
needed.

```python
class ResponseReviewer(PromptPlugin):
    stages = [PipelineStage.REVIEW]

    async def _execute_impl(self, context: PluginContext) -> None:
        if not context.has_response():
            return
        updated = context.response.replace("badword", "***")
        context.update_response(lambda _old: updated)
```

These examples can be imported and registered in a workflow for quick testing.
