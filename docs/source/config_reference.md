# Configuration Reference

## AdapterSettings

Configuration for adapter plugins.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| stages | list | None |  |
| auth_tokens | list | None |  |
| rate_limit | ForwardRef('RateLimitConfig | None') | None |  |
| audit_log_path | str | None | None |  |
| dashboard | bool | False |  |

## BreakerSettings

Circuit breaker settings for different resource types.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| database | ForwardRef('CircuitBreakerConfig') | None |  |
| external_api | ForwardRef('CircuitBreakerConfig') | None |  |
| file_system | ForwardRef('CircuitBreakerConfig') | None |  |

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
| server | ForwardRef('ServerConfig') | None |  |
| plugins | ForwardRef('PluginsSection') | None |  |
| workflow | ForwardRef('WorkflowSettings | None') | None |  |
| tool_registry | ForwardRef('ToolRegistryConfig') | None |  |
| runtime_validation_breaker | ForwardRef('CircuitBreakerConfig') | None |  |
| breaker_settings | ForwardRef('BreakerSettings') | None |  |

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
| outputs | ForwardRef('list[LogOutputConfig]') | None |  |

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
| dependencies | list | None |  |
| stage | ForwardRef('PipelineStage | None') | None |  |
| stages | ForwardRef('list[PipelineStage]') | None |  |

## PluginsSection

Collection of user-defined plugins grouped by category.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| infrastructure | ForwardRef('Dict[str, PluginConfig]') | None |  |
| resources | ForwardRef('Dict[str, PluginConfig]') | None |  |
| agent_resources | ForwardRef('Dict[str, PluginConfig]') | None |  |
| custom_resources | ForwardRef('Dict[str, PluginConfig]') | None |  |
| tools | ForwardRef('Dict[str, PluginConfig]') | None |  |
| adapters | ForwardRef('Dict[str, PluginConfig]') | None |  |
| prompts | ForwardRef('Dict[str, PluginConfig]') | None |  |

## RateLimitConfig

Request throttling settings for an adapter.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| requests | ConstrainedIntValue | 1 |  |
| interval | ConstrainedIntValue | 60 |  |

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

## WorkflowSettings

Mapping of pipeline stages to plugin names.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| stages | ForwardRef('Dict[str, list[str]]') | None |  |
