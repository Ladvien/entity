# Configuration Reference

## BreakerSettings

Circuit breaker settings for different resource types.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| database | ForwardRef('CircuitBreakerConfig') | Required |  |
| external_api | ForwardRef('CircuitBreakerConfig') | Required |  |
| file_system | ForwardRef('CircuitBreakerConfig') | Required |  |

## CircuitBreakerConfig

Circuit breaker configuration.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| failure_threshold | int | 3 |  |
| recovery_timeout | float | 60.0 |  |
| database | int | None | 3 |  |
| api | int | None | 5 |  |
| filesystem | int | None | 2 |  |

## EmbeddingModelConfig

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| name | str | Required |  |
| dimensions | int | None | None |  |

## EntityConfig

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| server | ForwardRef('ServerConfig') | Required |  |
| plugins | ForwardRef('PluginsSection') | Required |  |
| workflow | ForwardRef('Dict[str, list[str]] | None') | None |  |
| tool_registry | ForwardRef('ToolRegistryConfig') | Required |  |
| runtime_validation_breaker | ForwardRef('CircuitBreakerConfig') | Required |  |
| breaker_settings | ForwardRef('BreakerSettings') | Required |  |

## LLMConfig

Configuration model for the :class:`~entity.resources.llm.LLM`.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| provider | str | 'default' |  |

## LogOutputConfig

Configuration for a single logging output.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| type | str | 'console' |  |
| level | str | 'info' |  |
| path | str | None | None |  |
| host | str | None | None |  |
| port | int | None | None |  |
| max_size | int | None |  |  |
| backup_count | int | None |  |  |

## LoggingConfig

Settings controlling the :class:`LoggingResource`.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| host_name | str | socket.gethostname() |  |
| process_id | int | os.getpid() |  |
| outputs | ForwardRef('list[LogOutputConfig]') | Required |  |

## MemoryConfig

Configuration model for the :class:`~entity.resources.memory.Memory`.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| kv_table | str | 'memory_kv' |  |
| history_table | str | 'conversation_history' |  |

## PluginConfig

Configuration for a single plugin.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| type | str | Required |  |

## PluginsSection

Collection of user-defined plugins grouped by category.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| infrastructure | ForwardRef('Dict[str, PluginConfig]') | Required |  |
| resources | ForwardRef('Dict[str, PluginConfig]') | Required |  |
| agent_resources | ForwardRef('Dict[str, PluginConfig]') | Required |  |
| custom_resources | ForwardRef('Dict[str, PluginConfig]') | Required |  |
| tools | ForwardRef('Dict[str, PluginConfig]') | Required |  |
| adapters | ForwardRef('Dict[str, PluginConfig]') | Required |  |
| prompts | ForwardRef('Dict[str, PluginConfig]') | Required |  |

## ServerConfig

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| host | str | Required |  |
| port | int | Required |  |
| reload | bool | False |  |
| log_level | str | 'info' |  |

## StorageConfig

Configuration model for the :class:`~entity.resources.storage.Storage`.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| namespace | str | 'default' |  |

## ToolRegistryConfig

Options controlling tool execution.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| concurrency_limit | int | 5 |  |
