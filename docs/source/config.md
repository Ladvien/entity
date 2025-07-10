# Configuration

Only parameter updates can be reloaded at runtime. Any addition or removal of
plugins or resources requires restarting the agent.

Plugin execution order strictly follows the YAML listing. When the builder
loads from a configuration file it registers plugins in that sequence so they
run exactly as written.
