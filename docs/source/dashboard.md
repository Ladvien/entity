# Dashboard Adapter

`DashboardAdapter` extends `HTTPAdapter` to provide a small web UI for monitoring pipeline activity.

## Configuration

Enable the adapter in your YAML configuration:

```yaml
plugins:
  adapters:
    dashboard:
      type: plugins.builtin.adapters.dashboard:DashboardAdapter
      stages: [parse, deliver]
      dashboard: true
      state_log_path: ./state.log
      pipeline_config: ./config/dev.yaml
```

- `state_log_path` – JSONL file containing state transitions logged with `StateLogger`.
- `pipeline_config` – path to a pipeline config used for generating the stage diagram.

## Usage

Start your agent normally and visit `/dashboard` on the running server. The page displays the number of active pipelines, a diagram of the configured pipeline and the most recent state transitions.

The endpoint `/dashboard/transitions` returns raw transition data which can be used to build custom visualizations.
