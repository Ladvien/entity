# Example Stories

Each example demonstrates a small aspect of the framework. These short stories explain what to expect when running them.

## basic_agent
This minimal agent echoes the most recent user message. It registers a single `@agent.output` function and prints the final response. Run it with:

```bash
poetry run python examples/basic_agent/main.py
```

## default
`examples/default` shows the decorator-based API. A simple tool and output plugin are registered with `@agent.tool` and `@agent.output`. The agent calculates `2 + 2` and returns the result alongside the original message.

## default_setup
This variant uses the global `agent` instance. No configuration is required; the default resources are prepared automatically. It performs the same calculation as the `default` example.

## duckdb_memory_agent
This example introduces a custom `DuckDBMemory` resource. The agent increments a counter stored in a DuckDB database on each run and prints the current value.

## full_workflow
`examples/full_workflow` integrates multiple LLM providers with PostgreSQL, vector storage, logging, and metrics. It demonstrates how to register infrastructure resources and custom plugins for a complete workflow.

## intermediate_agent
This story chains a prompt plugin with a custom responder. The THINK stage collects a breakdown of the user's question. The responder outputs the final explanation.

## kitchen_sink
The kitchen sink agent executes a small ReAct loop. It calls the calculator tool, accumulates thoughts with `ctx.reflect()`, and replies with the final reasoning path.
