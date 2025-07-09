# Plugin Discovery Experiment

This experiment demonstrates a simple plugin loader that resolves
plugin dependencies.

Plugins placed inside a directory are scanned for subclasses of
`BasePlugin`. Dependencies declared through the `dependencies`
attribute are used to compute an execution order with
`DependencyGraph`.

The optional `hot_reload.py` script shows how you might watch a
directory for changes during development.

This is experimental code and should not be used in production.
