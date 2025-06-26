# Entity Framework Architecture Summary

## 🎯 Vision
A **Bevy-inspired plugin framework** for AI agents that's composable, extensible, and configuration-driven.

## 🏗️ Core Architecture

### Event Loop Pipeline with LLM Inference
```mermaid
flowchart TD
    Users[👤 Users] --> API[🌐 API]
    API --> IA[📥 Input Adapter]
    IA --> IP[🔄 Input Processing]
    IP --> PPP[🛠️ Prompt Pre-processing]
    PPP --> PP[✨ Prompt Processing]
    PP --> TR[🔧 Tool Registration]
    TR --> OP[📤 Output Processing]
    OP --> OA[📮 Output Adapter]
    
    %% LLM Inference Branch
    TR --> |recompile=True| LLM[🧠 LLM Inference]
    PP --> |recompile=True| LLM
    OP --> |recompile=True| LLM
    
    LLM --> TC{Tool Calls?}
    TC --> |Yes| TE[⚡ Tool Execution]
    TC --> |No| Response[📱 Response]
    TE --> |Results| IP
    
    OA --> |No recompile| Response
    
    %% Styling
    classDef input fill:#e3f2fd
    classDef processing fill:#fff3e0
    classDef llm fill:#f3e5f5
    classDef output fill:#e8f5e8
    classDef endpoints fill:#fce4ec
    classDef tools fill:#e8f5f0
    
    class Users,API,Response endpoints
    class IA,IP input
    class PPP,PP,TR processing
    class LLM,TC llm
    class OP,OA output
    class TE tools
```

### Pipeline Execution Model

The pipeline follows a **conditional loop pattern** with LLM inference:

1. **Linear Pipeline Execution**: All stages run once in order
2. **Recompile Check**: If any stage sets `context.recompile = True`, trigger LLM inference
3. **Tool Execution**: LLM tool calls execute immediately outside the pipeline
4. **Pipeline Restart**: Tool results restart pipeline at Input Processing stage (not Input Adapters)
5. **Iteration Limit**: `max_iterations` prevents infinite loops

```python
async def process_request(request):
    context = EventContext(request=request, input=[str(request)])
    
    for iteration in range(max_iterations):
        # Run pipeline stages in order
        await run_stage("input_processing", context)
        await run_stage("prompt_preprocessing", context) 
        await run_stage("prompt_processing", context)
        await run_stage("tool_registration", context)  # Tools register availability
        await run_stage("output_processing", context)
        
        # Check if any stage requested LLM inference
        if context.recompile:
            context.recompile = False
            
            # Call LLM with available tools
            llm_response = await llm.generate(
                prompt=context.prompt,
                tools=context.get_metadata("available_tools")
            )
            
            # Execute all tool calls immediately (Option A)
            if llm_response.has_tool_calls():
                for tool_call in llm_response.tool_calls:
                    tool_plugin = tool_registry.get(tool_call.name)
                    result = await tool_plugin.execute_function(tool_call.args)
                    context.add_input(f"Tool {tool_call.name}: {result}")
                
                # Restart pipeline at Input Processing with tool results
                continue
            else:
                # LLM provided final response
                context.response = llm_response.content
                break
        else:
            # No recompile requested, pipeline complete
            break
    
    return context.response
```

### Three-Layer Plugin System

#### **Resource Plugins** (Infrastructure - Enables System Function)
- **Database**: PostgreSQL, SQLite connections
- **LLM**: Ollama, OpenAI, Claude servers  
- **Memory**: Vector databases, Redis cache
- **TTS**: Text-to-speech services
- **Storage**: File systems, cloud storage
- **Logging**: Structured logging, metrics, tracing
- **Monitoring**: Health checks, performance metrics

#### **Tool Plugins** (Functionality - Performs Tasks for Users)
- **Weather**: Get current conditions, forecasts
- **Calculator**: Mathematical computations
- **Search**: Web search, document search
- **File Operations**: Read, write, process files
- **API Integrations**: Slack, email, custom APIs

**Tool Execution Model**: Tools register their schemas during the pipeline but execute **only when called by the LLM** via function calling. All tool calls from one LLM response execute immediately and in parallel.

#### **Prompt Plugins** (Processing - Controls Request Flow)
- **Strategies**: ReAct, Chain-of-Thought, Direct Response
- **Personality**: Sarcasm, loyalty, wit injection
- **Memory**: Context retrieval and storage
- **Output**: Formatting, validation, filtering

## 🔧 Key Components

### Shared Context
```python
class EventContext:
    input: List[str]          # Ordered conversation history ["user msg", "tool result", ...]
    response: Any             # Final output
    prompt: str               # Current prompt
    memory_context: str       # Retrieved context
    metadata: Dict            # Plugin data
    recompile: bool           # Trigger LLM reprocessing
    resources: ResourceRegistry  # Access to all resources
    trace_id: str             # Unique request identifier for logging
    metrics: MetricsCollector # Performance and usage metrics
    max_iterations: int       # Prevent infinite loops
```

### Plugin Observability & Logging
```python
class BasePlugin:
    def __init__(self):
        self.logger = None  # Injected during initialization
        
    async def execute(self, context: EventContext):
        # Automatic logging with trace ID
        self.logger.info(
            "Plugin execution started",
            plugin=self.__class__.__name__,
            trace_id=context.trace_id,
            stage=self.get_stage()
        )
        
        start_time = time.time()
        try:
            result = await self._execute_impl(context)
            
            # Automatic metrics collection
            context.metrics.record_plugin_duration(
                plugin=self.__class__.__name__,
                duration=time.time() - start_time
            )
            
            return result
        except Exception as e:
            self.logger.error(
                "Plugin execution failed",
                plugin=self.__class__.__name__,
                trace_id=context.trace_id,
                error=str(e),
                exc_info=True
            )
            raise
```

### Plugin Validation System
```python
class ValidationResult:
    success: bool
    error_message: str = None
    warnings: List[str] = []

class BasePlugin:
    dependencies = []  # List of registry keys that this plugin depends on
    
    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        """
        Pure configuration validation - no external dependencies.
        Validates:
        - Required config keys exist
        - Values are correct types/formats
        - URLs are well-formed
        - Numeric ranges are valid
        - No registry or cross-plugin concerns
        """
        return ValidationResult(success=True)
    
    @classmethod
    def validate_dependencies(cls, registry: ClassRegistry) -> ValidationResult:
        """
        Dependency validation - checks that declared dependencies exist in registry.
        Validates:
        - All items in cls.dependencies exist in registry
        - No circular dependency chains (using topological sort)
        - Plugin execution order can be determined
        
        Uses registry keys (YAML config names) for dependencies.
        """
        # Check all dependencies exist
        for dep in cls.dependencies:
            if not registry.has_plugin(dep):
                available = registry.list_plugins()
                return ValidationResult.error(f"{cls.__name__} requires '{dep}' but it's not registered. Available: {available}")
        
        return ValidationResult.success()
    
    @classmethod
    def validate_all(cls, config: Dict, registry: ClassRegistry) -> ValidationResult:
        """Convenience method for complete validation (config + dependencies)"""
        config_result = cls.validate_config(config)
        if not config_result.success:
            return config_result
        return cls.validate_dependencies(registry)
    
    @classmethod
    def from_dict(cls, config: Dict) -> 'Self':
        """
        Create plugin from config with CONFIG VALIDATION ONLY.
        
        WARNING: This does NOT validate dependencies. Use only for:
        - Testing with mocked dependencies
        - Development/prototyping
        - When dependencies are guaranteed to exist
        
        For production systems, use four-phase initialization.
        """
        result = cls.validate_config(config)
        if not result.success:
            raise ConfigurationError(f"{cls.__name__} config validation failed: {result.error_message}")
        return cls(config)
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'Self':
        """Parse YAML then delegate to from_dict (config validation only)"""
        config = yaml.safe_load(yaml_content)
        return cls.from_dict(config)
    
    @classmethod
    def from_json(cls, json_content: str) -> 'Self':
        """Parse JSON then delegate to from_dict (config validation only)"""
        config = json.loads(json_content)
        return cls.from_dict(config)
```

### Plugin Capabilities
- **Read/Write Context**: Plugins can modify any part of the request/response
- **Resource Access**: `context.resources.get("llm")` - request what you need
- **Short Circuit**: Skip remaining pipeline stages (like `continue` in loops)
- **Recompile**: Force LLM reprocessing after prompt changes
- **Tool Registration**: Tools register schemas but execute only when LLM calls them

## ⚙️ Configuration

### Four-Phase System Initialization
```python
# Phase 1: Class Registration (Metadata Only - Order Independent)
# Phase 2: Static Validation (All Classes Available - Fail Fast)
# Phase 3: Resource Initialization (Dependency Order with Cleanup)
# Phase 4: Plugin Instantiation (Everything Ready)

class SystemInitializer:
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'SystemInitializer':
        """
        Load entire system configuration from single YAML file.
        Handles environment variable interpolation at system level for security.
        """
        # 1. Load YAML content
        with open(yaml_path, 'r') as file:
            yaml_content = file.read()
        
        # 2. Interpolate ALL environment variables at system level (security)
        config = cls._interpolate_env_vars(yaml.safe_load(yaml_content))
        
        # 3. Return SystemInitializer with fully resolved config
        return cls(config)
    
    def get_resource_config(self, name: str) -> Dict:
        """Explicitly extract resource configuration"""
        return self.config["plugins"]["resources"][name]
    
    def get_tool_config(self, name: str) -> Dict:
        """Explicitly extract tool configuration"""
        return self.config["plugins"]["tools"][name]
    
    def get_adapter_config(self, name: str) -> Dict:
        """Explicitly extract adapter configuration"""
        return self.config["plugins"]["adapters"][name]
    
    def get_prompt_config(self, name: str) -> Dict:
        """Explicitly extract prompt configuration"""
        return self.config["plugins"]["prompts"][name]

    def initialize(self):
        with initialization_cleanup_context():
            # Phase 1: Register all plugin classes and extract dependency graph
            registry = ClassRegistry()
            dependency_graph = {}
            
            # Register resources
            for resource_name, resource_config in self.config["plugins"]["resources"].items():
                resource_class = import_plugin_class(resource_config.get("type", resource_name))
                registry.register_class(resource_class, resource_config, resource_name)
                dependency_graph[resource_name] = resource_class.dependencies
            
            # Register tools, adapters, prompts...
            for plugin_type in ["tools", "adapters", "prompts"]:
                for plugin_name, plugin_config in self.config["plugins"].get(plugin_type, {}).items():
                    plugin_class = import_plugin_class(plugin_config.get("type", plugin_name))
                    registry.register_class(plugin_class, plugin_config, plugin_name)
                    dependency_graph[plugin_name] = plugin_class.dependencies
            
            # Phase 2: Validate dependencies exist and detect circular dependencies
            self._validate_dependency_graph(registry, dependency_graph)
            
            # Phase 2 continued: Config validation for all plugins
            for plugin_class, config in registry.all_plugin_classes():
                config_result = plugin_class.validate_config(config)
                if not config_result.success:
                    raise SystemError(f"Config validation failed for {plugin_class.__name__}: {config_result.error_message}")
            
            # Phase 3: Initialize resources in dependency order (no validation needed - already done!)
            resource_registry = ResourceRegistry()
            for resource_class, config in registry.resource_classes():
                instance = resource_class(config)  # Direct instantiation
                await instance.initialize()
                resource_registry.add_resource(instance)
            
            # Phase 4: Instantiate tool and prompt plugins (no validation needed - already done!)
            plugin_registry = PluginRegistry()
            for plugin_class, config in registry.non_resource_classes():
                instance = plugin_class(config)  # Direct instantiation
                plugin_registry.add_plugin(instance)
            
            return plugin_registry, resource_registry
    
    def _validate_dependency_graph(self, registry: ClassRegistry, dep_graph: Dict[str, List[str]]):
        """
        Validate dependency graph: check existence and detect circular dependencies.
        Uses registry keys (YAML config names) for dependency resolution.
        """
        # 1. Check all dependencies exist
        for plugin_name, deps in dep_graph.items():
            for dep in deps:
                if not registry.has_plugin(dep):
                    available = registry.list_plugins()
                    raise SystemError(f"Plugin '{plugin_name}' requires '{dep}' but it's not registered. Available: {available}")
        
        # 2. Detect circular dependencies using topological sort (Kahn's algorithm)
        in_degree = {node: 0 for node in dep_graph}
        for node in dep_graph:
            for neighbor in dep_graph[node]:
                if neighbor in in_degree:  # Only count registered plugins
                    in_degree[neighbor] += 1
        
        queue = [node for node, degree in in_degree.items() if degree == 0]
        processed = []
        
        while queue:
            current = queue.pop(0)
            processed.append(current)
            
            for neighbor in dep_graph[current]:
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        # If we didn't process all nodes, there's a cycle
        if len(processed) != len(in_degree):
            cycle_nodes = [node for node in in_degree if node not in processed]
            raise SystemError(f"Circular dependency detected involving: {cycle_nodes}")
        
    @staticmethod
    def _interpolate_env_vars(config: Any) -> Any:
        """Recursively interpolate environment variables in configuration"""
        if isinstance(config, dict):
            return {k: SystemInitializer._interpolate_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [SystemInitializer._interpolate_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            value = os.environ.get(env_var)
            if value is None:
                raise EnvironmentError(f"Required environment variable {env_var} not found")
            return value
        else:
            return config
```

### Hierarchical YAML Configuration
```yaml
entity:
  entity_id: "jade"
  max_iterations: 500  # Prevent infinite pipeline loops
  name: "Jade"
  server:
    host: "0.0.0.0"
    port: 8000
    reload: false
    log_level: "info"

plugins:
  resources:
    database:
      type: postgres
      host: "192.168.1.104"
      port: 5432
      name: "memory"
      username: "${DB_USERNAME}"      # Environment variable interpolation
      password: "${DB_PASSWORD}"      # Resolved at system level for security
      db_schema: "entity"
      history_table: "chat_history"
      min_pool_size: 2
      max_pool_size: 10
      init_on_startup: true
    
    ollama:
      type: ollama_llm
      base_url: "http://192.168.1.110:11434"
      model: "llama3:8b-instruct-q6_K"
      temperature: 0.7
      top_p: 0.9
      top_k: 40
      repeat_penalty: 1.1
    
    logging:
      type: structured_logging
      level: "DEBUG"
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
      file_enabled: true
      file_path: "logs/entity.log"
      max_file_size: 10485760
      backup_count: 5
  
  tools:
    weather:
      type: weather_api
      api_key: "${WEATHER_API_KEY}"
      base_url: "https://api.weather.com"
      timeout: 30
    
    calculator:
      type: calculator
      precision: 10
  
  adapters:
    tts:
      type: speech_synthesis
      base_url: "http://192.168.1.110:8888"
      voice_name: "bf_emma"
      voice_sample_path: "voice_samples/ai_mee.wav"
      output_format: "wav"
      speed: 0.3
      cfg_weight: 0.9
      exaggeration: 0.5
      sample_rates: [44100, 48000, 22050, 16000, 8000]
      fade_out_samples: 2000
  
  prompts:
    chain_of_thought:
      type: chain_of_thought
      enable_reasoning: true
      max_steps: 5
    
    memory_retrieval:
      type: memory_retrieval
      max_context_length: 4000
      similarity_threshold: 0.7
```

## 🚀 Key Benefits

### For Users
- **No Code Changes**: New strategies via config only
- **Mix and Match**: Combine multiple prompt strategies
- **Resource Flexibility**: Works with/without optional resources
- **Easy Experimentation**: Swap plugins to test approaches
- **Order Independent**: Plugin configuration order doesn't matter

### For Developers  
- **Plugin Ecosystem**: Share and discover community plugins
- **Clean Testing**: Mock resources, test plugins in isolation
- **Extensible**: Add new resources and strategies without core changes
- **Composable**: Plugins build on each other's work
- **Separated Validation**: Test config parsing independently from dependency resolution
- **Optimal Performance**: Parallel tool execution, fewer LLM calls
- **Simple Mental Model**: "Register tools → LLM uses them → Done"

### For Operations
- **Configuration-Driven**: Different setups for dev/staging/prod
- **Fail Fast**: Static validation catches issues early
- **Observable**: Rich metadata from each plugin
- **Scalable**: Resources shared across all plugins
- **Environment Security**: Centralized environment variable interpolation
- **Explicit Configuration**: Clear, transparent config extraction

## 🔌 Plugin Examples

### Custom Weather Integration
```python
# 1. Create Tool Plugin (performs agent tasks)
class WeatherToolPlugin(ToolPlugin):
    dependencies = ["weather_api"]  # Depends on weather_api resource (matches YAML key)
    
    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        # Pure configuration validation - no external dependencies
        if not config.get("api_key"):
            return ValidationResult.error("Missing required config: api_key")
        
        # Validate URL format without making requests
        base_url = config.get("base_url", "https://api.weather.com")
        if not cls._is_valid_url(base_url):
            return ValidationResult.error(f"Invalid base_url: {base_url}")
        
        # Validate timeout is reasonable
        timeout = config.get("timeout", 30)
        if not isinstance(timeout, int) or timeout <= 0:
            return ValidationResult.error("timeout must be a positive integer")
        
        return ValidationResult.success()
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        # Simple URL validation without network calls
        return url.startswith(("http://", "https://"))
    
    def get_tool_name(self) -> str:
        return "get_weather"
    
    async def _execute_impl(self, context: EventContext):
        # Register tool schema for LLM function calling
        tools = context.get_metadata("available_tools", [])
        tools.append(self.get_tool_schema())
        context.set_metadata("available_tools", tools)
    
    async def execute_function(self, args: Dict) -> str:
        # Called when LLM makes function call
        api = self.resources.get("weather_api")
        return await api.get_forecast(args["location"])
    
    def get_tool_schema(self):
        return {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {"location": {"type": "string"}}
        }

# 2. Create Resource Plugin (provides infrastructure)
class WeatherAPIResourcePlugin(ResourcePlugin):
    dependencies = []  # No dependencies
    
    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        # Pure configuration validation
        if not config.get("api_key"):
            return ValidationResult.error("Weather API key not configured")
        
        # Validate URL format without making requests
        base_url = config.get("base_url", "https://api.weather.com")
        if not cls._is_valid_url(base_url):
            return ValidationResult.error(f"Invalid base_url: {base_url}")
        
        return ValidationResult.success()
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        # Simple URL validation without network calls
        return url.startswith(("http://", "https://"))
    
    def get_resource_name(self) -> str:
        return "weather_api"
    
    async def initialize(self, config) -> WeatherAPI:
        return WeatherAPI(config["api_key"], config.get("base_url"))

# 3. Create Logging Resource Plugin (provides observability)
class StructuredLoggingResourcePlugin(ResourcePlugin):
    dependencies = []  # No dependencies
    
    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        # Validate log level without instantiation
        valid_levels = ["DEBUG", "INFO", "WARN", "ERROR"]
        level = config.get("level", "INFO")
        if level not in valid_levels:
            return ValidationResult.error(f"Invalid log level '{level}'. Must be one of: {valid_levels}")
        
        # Validate output configuration
        valid_outputs = ["console", "file", "elasticsearch"]
        output = config.get("output", "console")
        if output not in valid_outputs:
            return ValidationResult.error(f"Invalid output '{output}'. Must be one of: {valid_outputs}")
        
        # If file output, check path is provided
        if output == "file" and not config.get("file_path"):
            return ValidationResult.error("file_path required when output is 'file'")
        
        # Validate file size limits
        if config.get("max_file_size") and config["max_file_size"] <= 0:
            return ValidationResult.error("max_file_size must be positive")
        
        return ValidationResult.success()
    
    def get_resource_name(self) -> str:
        return "logger"
    
    async def initialize(self, config) -> StructuredLogger:
        return StructuredLogger(
            level=config.get("level", "INFO"),
            output=config.get("output", "console"),
            format=config.get("format", "json"),
            service_name="entity-framework",
            file_path=config.get("file_path"),
            max_file_size=config.get("max_file_size"),
            backup_count=config.get("backup_count", 5)
        )

# 4. Example of Complex Dependencies
class ChainOfThoughtPlugin(PromptPlugin):
    dependencies = ["database", "logging"]  # Needs database for memory, logging for observability
    
    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        # Validate reasoning configuration
        max_steps = config.get("max_steps", 5)
        if not isinstance(max_steps, int) or max_steps <= 0:
            return ValidationResult.error("max_steps must be a positive integer")
        
        return ValidationResult.success()
```

## 🎨 Design Principles

1. **Configuration Over Code**: Behavior defined in YAML, not hardcoded
2. **Plugin Composition**: Multiple plugins work together seamlessly  
3. **Resource Agnostic**: Plugins work with/without optional dependencies
4. **Fail Gracefully**: Missing resources don't crash the system
5. **Pipeline Control**: Plugins can short-circuit or trigger reprocessing
6. **Shared State**: Rich context object for plugin collaboration
7. **Fail-Fast Validation**: All plugin dependencies validated statically before instantiation
8. **Observable by Design**: Structured logging, metrics, and tracing built into every plugin
9. **Order Independence**: Plugin configuration order doesn't matter - validation handles dependencies
10. **Configuration Flexibility**: Multiple config formats (YAML, JSON, Dict) with secure env interpolation
11. **Separation of Concerns**: Clear distinction between config validation and dependency validation
12. **Load-Time Validation**: Validation should be done at load time, reducing runtime errors
13. **Intuitive Mental Models**: Mental models should be intensely easy to understand
14. **Optimal Tool Execution**: Tools register capabilities but execute only when LLM requests them
15. **Performance First**: Parallel tool execution and minimal LLM calls for better performance

## 🌟 Real-World Usage

```yaml
# Development: Simple setup
entity:
  entity_id: "dev_agent"
  name: "Development Agent"
  max_iterations: 50

plugins:
  resources:
    database:
      type: sqlite
      file_path: "dev.db"
    llm:
      type: local_llm
      model: "llama3:8b"

# Production: Full stack with observability
entity:
  entity_id: "prod_agent"
  name: "Production Agent"
  max_iterations: 100

plugins:
  resources:
    database:
      type: postgresql
      host: "db.company.com"
      username: "${DB_USERNAME}"
      password: "${DB_PASSWORD}"
    llm:
      type: openai_gpt4
      api_key: "${OPENAI_API_KEY}"
    logging:
      type: structured_logging
      level: "INFO"
      output: "elasticsearch"
      format: "json"
    metrics:
      type: prometheus_metrics
      port: 9090
    tracing:
      type: jaeger_tracing
      endpoint: "http://jaeger:14268"

# Experimentation: A/B testing
plugins:
  prompts:
    reasoning:
      type: "chain_of_thought"    # Strategy A
      # type: "direct_response"   # Strategy B (commented out)
      enable_reasoning: true
```

## Project Structure

```txt
entity/
├── README.md
├── pyproject.toml
├── requirements.txt
├── setup.py

├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
│
├── entity/
│   ├── __init__.py
│   ├── version.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── context.py              # EventContext class
│   │   ├── event_loop.py           # Main event processing pipeline
│   │   ├── registry.py             # ClassRegistry, ResourceRegistry, PluginRegistry
│   │   ├── system.py               # SystemInitializer, four-phase initialization
│   │   ├── exceptions.py           # ConfigurationError, SystemError, etc.
│   │   └── cleanup.py              # initialization_cleanup_context
│   │
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── base.py                 # BasePlugin, ValidationResult
│   │   ├── resource.py             # ResourcePlugin base class
│   │   ├── tool.py                 # ToolPlugin base class
│   │   ├── prompt.py               # PromptPlugin base class
│   │   ├── adapter.py              # AdapterPlugin base class
│   │   │
│   │   ├── resources/
│   │   │   ├── __init__.py
│   │   │   ├── database/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── postgres.py     # PostgresResourcePlugin
│   │   │   │   ├── sqlite.py       # SQLiteResourcePlugin
│   │   │   │   └── models.py       # Database models, schemas
│   │   │   ├── llm/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ollama.py       # OllamaLLMResourcePlugin
│   │   │   │   ├── openai.py       # OpenAIResourcePlugin
│   │   │   │   ├── claude.py       # ClaudeResourcePlugin
│   │   │   │   └── base.py         # BaseLLMResource
│   │   │   ├── memory/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── vector.py       # VectorDatabaseResourcePlugin
│   │   │   │   ├── redis.py        # RedisResourcePlugin
│   │   │   │   └── cache.py        # CacheResourcePlugin
│   │   │   ├── storage/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── filesystem.py   # FileSystemResourcePlugin
│   │   │   │   ├── s3.py           # S3ResourcePlugin
│   │   │   │   └── gcs.py          # GoogleCloudStorageResourcePlugin
│   │   │   ├── logging/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── structured.py   # StructuredLoggingResourcePlugin
│   │   │   │   ├── elasticsearch.py # ElasticsearchLoggingResourcePlugin
│   │   │   │   └── formatters.py   # Log formatters
│   │   │   ├── monitoring/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── prometheus.py   # PrometheusResourcePlugin
│   │   │   │   ├── jaeger.py       # JaegerTracingResourcePlugin
│   │   │   │   └── health.py       # HealthCheckResourcePlugin
│   │   │   └── tts/
│   │   │       ├── __init__.py
│   │   │       ├── speech_synthesis.py # SpeechSynthesisResourcePlugin
│   │   │       └── elevenlabs.py   # ElevenLabsResourcePlugin
│   │   │
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── weather.py          # WeatherToolPlugin
│   │   │   ├── calculator.py       # CalculatorToolPlugin
│   │   │   ├── search/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── web.py          # WebSearchToolPlugin
│   │   │   │   └── document.py     # DocumentSearchToolPlugin
│   │   │   ├── file_operations.py  # FileOperationsToolPlugin
│   │   │   └── integrations/
│   │   │       ├── __init__.py
│   │   │       ├── slack.py        # SlackToolPlugin
│   │   │       ├── email.py        # EmailToolPlugin
│   │   │       └── api.py          # CustomAPIToolPlugin
│   │   │
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── strategies/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── react.py        # ReActPromptPlugin
│   │   │   │   ├── chain_of_thought.py # ChainOfThoughtPromptPlugin
│   │   │   │   └── direct.py       # DirectResponsePromptPlugin
│   │   │   ├── personality/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sarcasm.py      # SarcasmPromptPlugin
│   │   │   │   ├── loyalty.py      # LoyaltyPromptPlugin
│   │   │   │   └── wit.py          # WitPromptPlugin
│   │   │   ├── memory/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── retrieval.py    # MemoryRetrievalPromptPlugin
│   │   │   │   └── context.py      # ContextPromptPlugin
│   │   │   └── output/
│   │   │       ├── __init__.py
│   │   │       ├── formatting.py   # FormattingPromptPlugin
│   │   │       ├── validation.py   # ValidationPromptPlugin
│   │   │       └── filtering.py    # FilteringPromptPlugin
│   │   │
│   │   └── adapters/
│   │       ├── __init__.py
│   │       ├── input/
│   │       │   ├── __init__.py
│   │       │   ├── http.py         # HTTPInputAdapterPlugin
│   │       │   ├── websocket.py    # WebSocketInputAdapterPlugin
│   │       │   └── cli.py          # CLIInputAdapterPlugin
│   │       └── output/
│   │           ├── __init__.py
│   │           ├── http.py         # HTTPOutputAdapterPlugin
│   │           ├── websocket.py    # WebSocketOutputAdapterPlugin
│   │           ├── tts.py          # TTSOutputAdapterPlugin
│   │           └── cli.py          # CLIOutputAdapterPlugin
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py               # FastAPI server setup
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py             # Chat endpoints
│   │   │   ├── health.py           # Health check endpoints
│   │   │   └── admin.py            # Admin endpoints
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── logging.py          # Request logging middleware
│   │   │   ├── metrics.py          # Metrics collection middleware
│   │   │   └── cors.py             # CORS middleware
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── request.py          # Request models
│   │       ├── response.py         # Response models
│   │       └── config.py           # API configuration models
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py               # YAML/JSON config loading
│   │   ├── validator.py            # Configuration validation
│   │   ├── interpolation.py        # Environment variable interpolation
│   │   └── schema.py               # Configuration schema definitions
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py              # Logging utilities
│   │   ├── metrics.py              # Metrics collection utilities
│   │   ├── tracing.py              # Distributed tracing utilities
│   │   ├── dependency_graph.py     # Dependency graph validation
│   │   ├── import_utils.py         # Dynamic plugin import utilities
│   │   └── testing.py              # Testing utilities and fixtures
│   │
│   └── cli/
│       ├── __init__.py
│       ├── main.py                 # Main CLI entry point
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── run.py              # Run server command
│       │   ├── validate.py         # Validate configuration command
│       │   ├── init.py             # Initialize project command
│       │   └── plugin.py           # Plugin management commands
│       └── templates/
│           ├── config.yaml         # Default configuration template
│           ├── dev.yaml            # Development configuration template
│           └── prod.yaml           # Production configuration template
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # pytest fixtures and configuration
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── test_context.py
│   │   │   ├── test_event_loop.py
│   │   │   ├── test_registry.py
│   │   │   └── test_system.py
│   │   ├── plugins/
│   │   │   ├── test_base.py
│   │   │   ├── resources/
│   │   │   │   ├── test_database.py
│   │   │   │   ├── test_llm.py
│   │   │   │   └── test_logging.py
│   │   │   ├── tools/
│   │   │   │   ├── test_weather.py
│   │   │   │   └── test_calculator.py
│   │   │   └── prompts/
│   │   │       ├── test_chain_of_thought.py
│   │   │       └── test_memory_retrieval.py
│   │   ├── config/
│   │   │   ├── test_loader.py
│   │   │   └── test_validator.py
│   │   └── utils/
│   │       ├── test_dependency_graph.py
│   │       └── test_import_utils.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_full_pipeline.py
│   │   ├── test_plugin_composition.py
│   │   └── test_system_initialization.py
│   ├── fixtures/
│   │   ├── configs/
│   │   │   ├── minimal.yaml
│   │   │   ├── full.yaml
│   │   │   └── invalid.yaml
│   │   └── data/
│   │       ├── sample_requests.json
│   │       └── expected_responses.json
│   └── e2e/
│       ├── __init__.py
│       ├── test_api_endpoints.py
│       └── test_cli_commands.py
│
├── examples/
│   ├── README.md
│   ├── minimal/
│   │   ├── config.yaml
│   │   ├── run.py
│   │   └── README.md
│   ├── development/
│   │   ├── config.yaml
│   │   └── README.md
│   ├── production/
│   │   ├── config.yaml
│   │   └── README.md
│   ├── custom_plugins/
│   │   ├── my_custom_tool.py
│   │   ├── my_custom_resource.py
│   │   └── README.md
│   └── advanced/
│       ├── multi_agent_config.yaml
│       ├── a_b_testing_config.yaml
│       └── README.md
│
├── docs/
│   ├── README.md
│   ├── getting_started.md
│   ├── configuration.md
│   ├── plugin_development.md
│   ├── architecture.md
│   ├── api_reference.md
│   ├── deployment_guide.md
│   ├── troubleshooting.md
│   └── examples/
│       ├── creating_custom_plugins.md
│       ├── configuration_patterns.md
│       └── testing_strategies.md
│
├── scripts/
│   ├── setup_dev.sh
│   ├── run_tests.sh
│   ├── deploy.sh
│   └── benchmark.py
│
└── benchmarks/
    ├── __init__.py
    ├── performance/
    │   ├── test_plugin_overhead.py
    │   ├── test_system_initialization.py
    │   └── test_memory_usage.py
    └── load_testing/
        ├── locustfile.py
        └── scenarios/
            ├── basic_chat.py
            └── complex_workflow.py
```

## 🎯 Bottom Line

**Entity Framework = Bevy for AI Agents**

- **Three Plugin Types**: Resources (infrastructure), Tools (user functions), Prompts (processing)
- **Infrastructure**: Clean separation between enabling vs performing
- **Composable**: Mix and match capabilities via configuration  
- **Testable**: Clean separation, easy mocking, isolated testing
- **Production-Ready**: Graceful degradation, rich observability
- **Developer-Friendly**: Clear patterns, shared community plugins
- **Performance-Optimized**: Parallel tool execution, minimal LLM calls
- **Conversation-Aware**: Pipeline restarts with conversation history

**Result**: Build AI agents like assembling LEGO blocks - flexible, reusable, and fun! 🧩

### Updated Pipeline Flow

```mermaid
graph TB
    %% Simplified System Architecture
    Users[👤 Users] --> API[🌐 API]
    API --> EL[🔄 Event Loop]
    EL --> CTX[📋 Context]
    EL --> RR[🏪 Registry]
    
    %% Three Plugin Layers
    RR --> Resources[📦 Resources<br/>DB, LLM, Cache]
    EL --> Tools[🛠️ Tools<br/>Weather, Calc, Search]
    EL --> Prompts[✨ Prompts<br/>CoT, ReAct, Memory]
    
    %% Styling
    classDef core fill:#f3e5f5
    classDef plugins fill:#e8f5e8
    
    class API,EL,CTX,RR core
    class Resources,Tools,Prompts plugins
```

### Tool Execution Flow

```mermaid
flowchart LR
    %% Updated Request Flow with Tool Execution
    User[👤 User] --> Input[📥 Input Processing]
    Input --> Prompts[✨ Prompt Processing]
    Prompts --> ToolReg[🔧 Tool Registration]
    ToolReg --> |recompile=True| LLM[🧠 LLM Inference]
    LLM --> ToolCalls{Tool Calls?}
    ToolCalls --> |Yes| ToolExec[⚡ Tool Execution<br/>All tools in parallel]
    ToolCalls --> |No| Output[📤 Output Processing]
    ToolExec --> |Results| Input
    Output --> Response[📱 Response]
    
    %% Short circuits
    Input -.-> Output
    Prompts -.-> Output
```

### Conversation State Management

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant E as Event Loop
    participant P as Pipeline
    participant L as LLM
    participant T as Tools
    
    U->>A: "Weather in NYC and calculate 25+17"
    A->>E: Start processing
    E->>P: Run pipeline stages
    P->>P: Tools register schemas
    P->>E: recompile=True
    E->>L: Call LLM with tools
    L->>E: "Call get_weather('NYC') and calculate('25+17')"
    E->>T: Execute both tools in parallel
    T->>E: ["sunny, 72°F", "42"]
    E->>P: Restart with tool results
    P->>E: recompile=True
    E->>L: Call LLM with conversation + results
    L->>E: "NYC is sunny 72°F, and 25+17=42"
    E->>A: Final response
    A->>U: Complete answer
```