from importlib import import_module

PluginAuditor = import_module(
    "plugins.contrib.infrastructure.sandbox.audit"
).PluginAuditor
