# Plugin Examples

The `src/plugins/examples/` directory contains minimal plugins for each pipeline stage.
These demonstrate how to interact with the `PluginContext` and which methods
are appropriate for different stages.

## InputLogger

`InputLogger` runs during the **INPUT** stage and saves the raw user message for
later steps.

```{literalinclude} ../../src/plugins/examples/input_logger.py
:language: python
:caption: InputLogger
```

## MessageParser

`MessageParser` executes in the **PARSE** stage and normalizes the user's
message.

```{literalinclude} ../../src/plugins/examples/message_parser.py
:language: python
:caption: MessageParser
```

## ResponseReviewer

`ResponseReviewer` runs in the **REVIEW** stage to modify the final response if
needed.

```{literalinclude} ../../src/plugins/examples/response_reviewer.py
:language: python
:caption: ResponseReviewer
```

These examples can be imported and registered in a workflow for quick testing.
