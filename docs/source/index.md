# Entity Pipeline Documentation

Welcome to the Entity Pipeline framework. These pages explain how to configure an agent, write plugins, and deploy the system.

```{include} ../../README.md
:relative-images:
:start-after: <!-- start quick_start -->
:end-before: <!-- end quick_start -->
```

## Documentation Map

### Getting Started
- [Quick start](quick_start.md)
- [Configuration cheat sheet](config_cheatsheet.md)

### Plugin Development
- [Plugin cheat sheet](plugin_cheatsheet.md)
- [Detailed guide](plugin_guide.md)
- [Naming conventions](plugins.md)
- [Developer examples](developer_examples.md)

### Architecture
- [Architecture overview](../../architecture/overview.md)
- [Components overview](components_overview.md)
- [Deliver-stage adapters](components_overview.md#deliver-stage-adapters)

### Reference
- [Context API](context.md)
- [API reference](api_reference.md)
- [Advanced usage](advanced_usage.md)
- [Module map](module_map.md)
- [Error handling](error_handling.md)
- [Troubleshooting](troubleshooting.md)

### Deployment
- [AWS deployment](deploy_aws.md)
- [Local](deploy_local.md)
- [Docker](deploy_docker.md)
- [Cloud](deploy_cloud.md)
- [Production guide](deploy_production.md)
- [Migration guide](migration_guide.md)

```{toctree}
:hidden:
quick_start
tutorial_setup
tutorial_first_pipeline
config
config_cheatsheet
plugin_cheatsheet
plugin_guide
developer_examples
context
security_config
logging
state_logging
advanced_usage
module_map
error_handling
troubleshooting
deploy_aws
deploy_local
deploy_docker
deploy_cloud
deploy_production
migration_guide
principle_checklist
apidocs/index
api_reference
components_overview
architecture
components_overview
plugins
tools
```
