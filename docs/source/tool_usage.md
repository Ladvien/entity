# Tool Usage - Give Your Agent Superpowers

## Tools Transform Agents from Chatbots to Doers

Entity Framework's tool system lets agents interact with the real world - search the web, manipulate files, call APIs, run calculations, and more. Tools execute during the **DO** stage of the 6-stage pipeline.

## Quick Example: Calculator Tool

```python
# Without tools: Agent can only talk about math
agent = Agent(resources=load_defaults())
await agent.chat("What's 37 * 89?")
# "To calculate 37 × 89, I would multiply... the answer is approximately..."

# With tools: Agent actually calculates
from entity.plugins.examples.calculator import Calculator

workflow = {
    "input": ["entity.plugins.defaults.InputPlugin"],
    "think": ["entity.plugins.defaults.ThinkPlugin"],
    "do": ["entity.plugins.examples.calculator.Calculator"],  # Tool!
    "output": ["entity.plugins.defaults.OutputPlugin"]
}

agent = Agent.from_workflow_dict(workflow)
await agent.chat("37 * 89")
# "3293"  # Actual calculated result!
```

## How Tools Work in Entity

Tools are plugins that execute during the **DO** stage:

```
INPUT → PARSE → THINK → 🔧 DO (Tools Execute Here) → REVIEW → OUTPUT
```

### Tool Architecture

```python
from entity.plugins.tool import ToolPlugin
from entity.workflow.executor import WorkflowExecutor

class MyCustomTool(ToolPlugin):
    """Your tool that does something useful."""

    supported_stages = [WorkflowExecutor.DO]  # Tools run in DO stage
    dependencies = ["file_storage", "llm"]    # Required resources

    async def _execute_impl(self, context):
        # Access the message
        query = context.message

        # Use resources
        storage = self.resources["file_storage"]

        # Do the actual work
        result = await perform_action(query)

        # Return result for next stage
        return result
```

## Built-in Tool Examples

### Web Search Tool
```python
class WebSearchTool(ToolPlugin):
    """Search the web for current information."""

    supported_stages = [WorkflowExecutor.DO]
    dependencies = ["llm"]

    async def _execute_impl(self, context):
        query = context.message

        # Simulate web search (real implementation would use API)
        results = await search_web(query)

        # Format results
        formatted = "\n".join([
            f"- {r['title']}: {r['snippet']}"
            for r in results[:5]
        ])

        return f"Search results for '{query}':\n{formatted}"
```

### File Operations Tool
```python
class FileOperationsTool(ToolPlugin):
    """Read, write, and manipulate files."""

    supported_stages = [WorkflowExecutor.DO]
    dependencies = ["file_storage"]

    async def _execute_impl(self, context):
        command = context.message
        storage = self.resources["file_storage"]

        if command.startswith("read:"):
            filename = command[5:].strip()
            content = await storage.read(filename)
            return f"File contents:\n{content}"

        elif command.startswith("write:"):
            parts = command[6:].split("|", 1)
            filename, content = parts[0].strip(), parts[1]
            await storage.write(filename, content)
            return f"Wrote {len(content)} bytes to {filename}"

        return "Unknown file operation"
```

### API Call Tool
```python
class APICallTool(ToolPlugin):
    """Make HTTP API calls."""

    supported_stages = [WorkflowExecutor.DO]

    async def _execute_impl(self, context):
        import aiohttp
        import json

        # Parse API call from message
        data = json.loads(context.message)

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=data.get("method", "GET"),
                url=data["url"],
                json=data.get("body"),
                headers=data.get("headers", {})
            ) as response:
                result = await response.json()

        return json.dumps(result, indent=2)
```

## Combining Multiple Tools

### Sequential Tool Chain
```yaml
# weather_reporter.yaml
workflow:
  do:
    # Tools execute in order
    - GetLocationTool      # First: Get user's location
    - WeatherAPITool       # Then: Fetch weather for location
    - FormatWeatherTool    # Finally: Format nicely
```

### Conditional Tool Selection
```python
class SmartToolSelector(ToolPlugin):
    """Choose the right tool based on the query."""

    async def _execute_impl(self, context):
        query = context.message.lower()

        if "calculate" in query or "math" in query:
            return await Calculator(self.resources).execute(context)
        elif "search" in query or "find" in query:
            return await WebSearchTool(self.resources).execute(context)
        elif "file" in query or "save" in query:
            return await FileOperationsTool(self.resources).execute(context)
        else:
            return "No appropriate tool found for this query"
```

## Tool Safety and Sandboxing

Entity provides sandboxed execution for tools:

```python
from entity.tools.sandbox import SandboxedToolRunner

class PotentiallyDangerousTool(ToolPlugin):
    """Tool that needs safety constraints."""

    async def _execute_impl(self, context):
        runner = SandboxedToolRunner(
            timeout=5.0,        # 5 second timeout
            memory_mb=100       # 100MB memory limit
        )

        # Run with constraints
        result = await runner.run(
            self.dangerous_operation,
            context.message
        )

        return result
```

## Creating Custom Tools

### Step 1: Define the Tool
```python
# my_tools.py
from entity.plugins.tool import ToolPlugin
from entity.workflow.executor import WorkflowExecutor

class StockPriceTool(ToolPlugin):
    """Get current stock prices."""

    supported_stages = [WorkflowExecutor.DO]

    async def _execute_impl(self, context):
        symbol = context.message.strip().upper()

        # Mock implementation (use real API)
        prices = {
            "AAPL": 175.43,
            "GOOGL": 141.28,
            "MSFT": 378.85
        }

        price = prices.get(symbol, "Unknown symbol")
        return f"{symbol}: ${price}"
```

### Step 2: Register in Workflow
```yaml
# stock_agent.yaml
resources:
  llm:
    system_prompt: "You are a financial assistant."

workflow:
  input:
    - entity.plugins.defaults.InputPlugin
  think:
    - entity.plugins.defaults.ThinkPlugin
  do:
    - my_tools.StockPriceTool  # Your custom tool!
  output:
    - entity.plugins.defaults.OutputPlugin
```

### Step 3: Use the Agent
```python
agent = Agent.from_config("stock_agent.yaml")
response = await agent.chat("AAPL")
# "AAPL: $175.43"
```

## Advanced Tool Patterns

### Tool with State
```python
class SessionAwareTool(ToolPlugin):
    """Tool that maintains state across calls."""

    def __init__(self, resources):
        super().__init__(resources)
        self.call_count = 0
        self.history = []

    async def _execute_impl(self, context):
        self.call_count += 1
        self.history.append(context.message)

        return f"Call #{self.call_count}: Processed {context.message}"
```

### Tool with External Dependencies
```python
class DatabaseTool(ToolPlugin):
    """Tool that queries a database."""

    dependencies = ["database"]  # Requires database resource

    async def _execute_impl(self, context):
        db = self.resources["database"]

        # Parse SQL from message
        query = context.message

        # Execute safely
        if self._is_safe_query(query):
            results = await db.execute(query)
            return self._format_results(results)
        else:
            return "Query not allowed for safety reasons"
```

### Tool with LLM Integration
```python
class SmartSummarizerTool(ToolPlugin):
    """Tool that uses LLM to summarize content."""

    dependencies = ["llm", "file_storage"]

    async def _execute_impl(self, context):
        filename = context.message

        # Read file
        storage = self.resources["file_storage"]
        content = await storage.read(filename)

        # Use LLM to summarize
        llm = self.resources["llm"]
        summary = await llm.generate(
            prompt=f"Summarize this text:\n{content}",
            max_tokens=200
        )

        return summary
```

## Tool Configuration

### Basic Tool Config
```yaml
workflow:
  do:
    - entity.plugins.examples.calculator.Calculator:
        precision: 2  # Round to 2 decimal places
        max_value: 1000000  # Prevent overflow
```

### Advanced Tool Config
```yaml
workflow:
  do:
    - WebSearchTool:
        api_key: ${SEARCH_API_KEY}  # From environment
        max_results: 10
        safe_search: true

    - FileOperationsTool:
        allowed_directories:
          - "/tmp"
          - "./workspace"
        max_file_size: 10485760  # 10MB

    - APICallTool:
        allowed_domains:
          - "api.example.com"
          - "data.service.com"
        timeout: 30
        retry_count: 3
```

## Testing Your Tools

```python
import pytest
from entity.plugins.context import Context

@pytest.mark.asyncio
async def test_calculator_tool():
    # Create tool
    tool = Calculator(resources={})

    # Create context
    context = Context(
        message="2 + 2",
        resources={},
        user_id="test"
    )

    # Execute
    result = await tool.execute(context)

    # Verify
    assert result == "4"

@pytest.mark.asyncio
async def test_tool_error_handling():
    tool = Calculator(resources={})
    context = Context(message="invalid", resources={}, user_id="test")

    with pytest.raises(ValueError):
        await tool.execute(context)
```

## Best Practices

### DO: Make Tools Focused
✅ One tool = one clear purpose
✅ `StockPriceTool` - just gets prices
❌ `FinancialTool` - does everything financial

### DO: Handle Errors Gracefully
```python
async def _execute_impl(self, context):
    try:
        result = await risky_operation()
        return result
    except SpecificError as e:
        return f"Could not complete: {e}"
    except Exception:
        return "An unexpected error occurred"
```

### DO: Validate Input
```python
async def _execute_impl(self, context):
    query = context.message

    # Validate before executing
    if not self._is_valid_query(query):
        return "Invalid query format. Expected: symbol:AAPL"

    # Safe to proceed
    return await self._fetch_data(query)
```

### DON'T: Block the Event Loop
❌ `time.sleep(5)` - Blocks everything
✅ `await asyncio.sleep(5)` - Non-blocking

### DON'T: Expose Sensitive Data
❌ Return API keys or passwords
❌ Log sensitive information
✅ Use environment variables
✅ Sanitize output

## Tool Categories

### Information Tools
- Web search
- Database queries
- API calls
- File reading

### Action Tools
- File writing
- Email sending
- Task creation
- System commands

### Analysis Tools
- Calculations
- Data processing
- Image analysis
- Text extraction

### Integration Tools
- Slack posting
- GitHub actions
- Calendar management
- CRM updates

## Quick Start: Your First Tool

1. **Create `word_counter.py`**:
```python
from entity.plugins.tool import ToolPlugin
from entity.workflow.executor import WorkflowExecutor

class WordCounterTool(ToolPlugin):
    supported_stages = [WorkflowExecutor.DO]

    async def _execute_impl(self, context):
        text = context.message
        word_count = len(text.split())
        char_count = len(text)

        return f"Words: {word_count}, Characters: {char_count}"
```

2. **Create `config.yaml`**:
```yaml
resources:
  llm:
    system_prompt: "You are a text analysis assistant."

workflow:
  input: ["entity.plugins.defaults.InputPlugin"]
  do: ["word_counter.WordCounterTool"]
  output: ["entity.plugins.defaults.OutputPlugin"]
```

3. **Use it**:
```python
agent = Agent.from_config("config.yaml")
result = await agent.chat("The quick brown fox jumps over the lazy dog")
# "Words: 9, Characters: 44"
```

## Next Steps

- **[Memory Systems](memory_systems.md)**: Tools that remember
- **[Custom Plugin Development](plugin_development.md)**: Advanced tool creation
- **[Production Deployment](production_deployment.md)**: Tools at scale

Remember: **Tools turn your agent from advisor to actor!**
