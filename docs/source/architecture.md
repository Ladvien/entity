# Architecture Overview

The Entity Pipeline Framework uses a single execution pipeline with explicit
stages. Plugins implement each stage and provide reusable behavior. The default
agent stores conversations in a DuckDB database that runs entirely in memory so
you can start experimenting without setting up external services.

## Pipeline Stages
- **parse** – validate input and load context
- **think** – reason and plan
- **do** – execute tools and actions
- **review** – format and validate responses
- **deliver** – send output to the user
- **error** – handle failures gracefully

After each pass through these stages, the pipeline examines `state.response`.
If the response is still empty, the stages repeat until a response exists or
`max_iterations` is hit. By default the framework allows five iterations. Once
this limit is exceeded, the pipeline jumps to the `error` stage. The limit can
be overridden by passing a different value for `max_iterations` to
`execute_pipeline`.

## Plugin Layers
1. **Resource plugins** – databases, LLMs and storage backends
2. **Tool plugins** – execute tasks such as search or math
3. **Prompt plugins** – control reasoning strategies and memory
4. **Adapter plugins** – handle input and output interfaces
5. **Failure plugins** – present errors and log issues

Every resource is registered under a single name so configuration remains small
and mental models stay easy to grasp.

## Plugin Lifecycle and Pipeline Stages
.. mermaid:: diagrams/plugin_lifecycle.mmd

## Design Principles
1. Progressive disclosure: simple things stay simple, complex things are possible
2. Async-first with predictable execution order. YAML order determines plugin execution.
3. Runtime reconfiguration with fail‑fast validation
4. Clear stage boundaries and structured logging
5. One canonical name per resource

Structured logging is enabled through ``LoggingAdapter`` which writes JSON lines
for each pipeline stage.

## Network Architecture
Backend services communicate over HTTP using JSON messages. Web
interfaces may rely on WebSockets, while command-line tools use
standard input and output.

For additional diagrams and examples see the ADRs in `docs/adr/`.

## Framework Overview Diagram
.. mermaid:: diagrams/overall_architecture.mmd


## Benchmark Results
The performance suite currently fails to run due to circular import errors.
Example output:
```
ImportError: cannot import name 'Resource' from partially initialized module 'entity.core.resources'
```

Once the imports are resolved, the `pytest-benchmark` plugin can capture
timing metrics for each pipeline stage.

## Zero-Config AWS Startup

a helper script can spin up a minimal AWS stack and run a pipeline with almost
no configuration. It provisions an S3 bucket and IAM role before starting the
agent. Behavior is defined by
a **Workflow** object:

```python
from my_workflows import QuickstartWorkflow
from pipeline import Pipeline

workflow = QuickstartWorkflow(prompt="my_prompts:QuickstartPrompt")
pipeline = Pipeline(approach=workflow)
```

The pipeline loops through `PARSE → THINK → DO → REVIEW → DELIVER` until a
plugin calls `set_response`, illustrating the hybrid pipeline–state machine model.
Because the workflow defines plugin selection, you can launch on AWS without a
YAML file and later swap in custom stages as needed. Pass different plugin
arguments when creating the workflow to reuse the same class across
environments.
