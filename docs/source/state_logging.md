# Pipeline State Logging

The pipeline can record the intermediate `PipelineState` after each stage. Enable logging by passing `--state-log <file>` when running the CLI.

```bash
poetry run entity-cli --config config/dev.yaml --state-log states.jsonl
```

Each entry is saved as JSON Lines with timestamp, pipeline id and stage. Replay the log with:

```bash
poetry run entity-cli replay-log states.jsonl
```


You can also log states programmatically using :class:`StateLogger`:

```python
from entity.core.state_logger import StateLogger
from pipeline.pipeline import execute_pipeline

logger = StateLogger("states.jsonl")
result = asyncio.run(execute_pipeline("hi", capabilities, state_logger=logger))
logger.close()
```

Old `state_file` and `snapshots_dir` parameters were removed. Use the logger instead to capture state transitions.

This prints the stored states with a short delay allowing you to inspect the pipeline flow.
