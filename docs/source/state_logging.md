# Pipeline State Logging

The pipeline can record the intermediate `PipelineState` after each stage. Enable logging by passing `--state-log <file>` when running the CLI.

```bash
poetry run python src/cli.py --config config/dev.yaml --state-log states.jsonl
```

Each entry is saved as JSON Lines with timestamp, pipeline id and stage. Replay the log with:

```bash
poetry run python src/cli.py replay-log states.jsonl
```

This prints the stored states with a short delay allowing you to inspect the pipeline flow.
