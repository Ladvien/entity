# Plugin Discovery Experiment

This experiment demonstrates a simple plugin loader that resolves
plugin dependencies and supports hot-reload using `watchdog`.

Plugins placed inside a directory are scanned for subclasses of
`BasePlugin`. Dependencies declared through the `dependencies`
attribute are used to compute an execution order with
`DependencyGraph`.

The `hot_reload.py` script watches the directory for changes and
reloads plugins when files are added, removed or modified.
