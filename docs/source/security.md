# Sandbox Security

This project can run plugins inside isolated Docker containers. Each plugin must
provide a `plugin.toml` manifest defining required resources and runtime limits.
The :class:`user_plugins.infrastructure.sandbox.DockerSandboxRunner` applies CPU and memory limits
based on the manifest and verifies the plugin signature before execution. The
runner uses :class:`infrastructure.DockerInfrastructure` so you can also build
a Docker image for your agent.

To validate manifests outside of runtime, use :class:`user_plugins.infrastructure.sandbox.PluginAuditor`.
It checks requested resources against a whitelist and reports any violations.
