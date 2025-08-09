# 03 - Tool Usage 🔧

**Give Your Agent Superpowers with Built-in Tools**

Learn how to extend your agent's capabilities using Entity's powerful tool system for web search, calculations, file operations, and more.

## What This Example Teaches

- 🔧 **Built-in tool integration** (web search, calculator, file operations)
- ⚙️ **Tool configuration** and customization
- 🔗 **Tool chaining** for complex workflows
- 🛡️ **Safe tool execution** with sandboxing
- 📊 **Tool result processing** and formatting

## Available Built-in Tools

Entity comes with powerful built-in tools:

### 🌐 **Web Search Tool**
- Search the internet for current information
- Filter results by relevance and recency
- Automatic content extraction and summarization

### 🧮 **Calculator Tool**
- Mathematical calculations and expressions
- Support for complex operations and functions
- Safe evaluation with result validation

### 📁 **File Operations Tool**
- Read and write files safely
- Directory listing and navigation
- Content analysis and processing

### 📊 **Data Analysis Tool**
- Process CSV and JSON data
- Generate summaries and insights
- Create simple visualizations

## The Complete Example

```python
#!/usr/bin/env python3
"""
Tool Usage Example - Agent with Superpowers

This example demonstrates how to give your Entity agent
powerful capabilities through the built-in tool system.
"""

import asyncio
from pathlib import Path
from entity import Agent

async def main():
    \"\"\"Run an agent equipped with powerful tools.\"\"\"

    print("🔧 Entity Agent with Tools")
    print("=" * 30)
    print()
    print("This agent is equipped with:")
    print("🌐 Web Search - Find current information online")
    print("🧮 Calculator - Perform complex calculations")
    print("📁 File Operations - Read, write, and analyze files")
    print("📊 Data Analysis - Process and understand data")
    print()

    # Load configuration with tools enabled
    config_path = Path(__file__).parent / "tools_config.yaml"

    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return

    try:
        agent = Agent.from_config(str(config_path))

        print("✅ Tool-enabled agent loaded!")
        print()
        print("💬 Try these example requests:")
        print("   • 'Search for the latest Python 3.12 features'")
        print("   • 'Calculate the compound interest on $1000 at 5% for 10 years'")
        print("   • 'Read the file data.csv and summarize the contents'")
        print("   • 'Find information about Entity Framework and calculate ROI'")
        print()
        print("🚀 Your tool-powered agent is ready!")
        print("=" * 30)

        await agent.chat("")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration (`tools_config.yaml`)

```yaml
# Agent with Tools Configuration
# Enables web search, calculator, file operations, and data analysis

# Agent role optimized for tool usage
role: |
  You are a helpful AI assistant with access to powerful tools.

  Your approach:
  - Always consider which tools could help answer the user's question
  - Use web search for current information and research
  - Use calculator for any mathematical operations
  - Use file operations when users mention files or data
  - Explain what tools you're using and why
  - Present results clearly and offer follow-up analysis

  When using tools:
  - Tell the user what you're going to do before using a tool
  - Explain the results you got from each tool
  - Combine information from multiple tools when relevant
  - Offer additional analysis or related searches

# Tool configuration - enables specific tools with settings
tools:
  web_search:
    enabled: true
    max_results: 5
    include_snippets: true
    timeout_seconds: 30

  calculator:
    enabled: true
    precision: 10
    allow_functions: true  # sin, cos, log, etc.

  file_operations:
    enabled: true
    allowed_extensions: ['.txt', '.csv', '.json', '.md', '.py']
    max_file_size_mb: 10
    read_only: false  # Allow file writing (be careful!)

  data_analysis:
    enabled: true
    max_rows: 10000
    generate_summary: true
    create_visualizations: false  # Requires additional setup

# Resource configuration
resources:
  llm:
    temperature: 0.1  # Lower temperature for tool usage accuracy
    max_tokens: 3000  # Allow for detailed tool results
```

## Example Conversations

### 🌐 Web Search Example
```
👤 You: Search for the latest news about artificial intelligence breakthroughs in 2024

🤖 Agent: I'll search for the latest AI breakthroughs in 2024 for you.

🔍 Using Web Search Tool: "artificial intelligence breakthroughs 2024 latest news"

Based on my search, here are the major AI breakthroughs in 2024:

1. **GPT-4 Turbo with Vision**: OpenAI released an enhanced model with improved multimodal capabilities...

2. **Google's Gemini Ultra**: Achieved human-level performance on MMLU benchmarks...

3. **Anthropic's Constitutional AI**: Major advances in AI safety and alignment...

4. **Open Source Models**: Significant improvements in Llama 2, Mistral, and other open models...

Would you like me to search for more specific information about any of these breakthroughs?
```

### 🧮 Calculator Example
```
👤 You: If I invest $5000 at 7% annual interest compounded monthly for 15 years, how much will I have?

🤖 Agent: I'll calculate the compound interest for your investment scenario.

🧮 Using Calculator Tool: A = P(1 + r/n)^(nt)
Where: P=$5000, r=0.07, n=12, t=15

Calculating: 5000 * (1 + 0.07/12)^(12*15)
Result: $14,544.75

Your $5,000 investment at 7% annual interest compounded monthly for 15 years will grow to approximately **$14,544.75**.

This represents a total return of $9,544.75 (191% gain) on your initial investment.

Would you like me to calculate different scenarios or show you how the growth progresses year by year?
```

### 📁 File Operations Example
```
👤 You: Read my sales_data.csv file and tell me what insights you can find

🤖 Agent: I'll analyze your sales data file for you.

📁 Using File Operations Tool: Reading "sales_data.csv"

📊 Using Data Analysis Tool: Processing sales data...

## Sales Data Analysis

**File Summary:**
- 1,247 sales records from January 2024 to November 2024
- Columns: Date, Product, Category, Amount, Customer_ID, Region

**Key Insights:**
1. **Total Sales**: $847,392 across all products
2. **Top Product**: Premium Widget ($127,439 - 15% of total)
3. **Best Month**: October 2024 ($94,231)
4. **Top Region**: West Coast (34% of sales)
5. **Average Order**: $679.45

**Trends:**
- 📈 Sales grew 23% from Q1 to Q3
- 🎯 Premium products account for 62% of revenue
- 🌊 Clear seasonal pattern with Q4 spike

Would you like me to dive deeper into any specific aspect of your sales data?
```

## Tool Chaining Example

The real power comes from combining multiple tools:

```
👤 You: Research the current market cap of Apple, then calculate what percentage that represents of the total US GDP

🤖 Agent: I'll help you research Apple's market cap and compare it to US GDP.

🔍 Step 1: Searching for Apple's current market cap...
Result: Apple's market cap is approximately $2.89 trillion (as of latest data)

🔍 Step 2: Searching for current US GDP...
Result: US GDP is approximately $27.36 trillion (2023 annual figure)

🧮 Step 3: Calculating the percentage...
Calculation: (2.89 / 27.36) × 100 = 10.56%

## Analysis Results

**Apple's market cap represents approximately 10.56% of the total US GDP.**

This is remarkable because:
- A single company represents over 10% of the entire US economic output
- Apple's valuation exceeds the GDP of most countries
- This shows the concentration of value in big tech companies

For context, Apple's market cap is larger than the entire GDP of:
- Canada ($2.14T)
- India ($2.39T)
- United Kingdom ($2.76T)

Would you like me to compare this with other major tech companies or historical data?
```

## Creating Custom Tools

You can also create your own tools:

```python
# custom_tools.py
from entity.tools import register_tool
import requests

@register_tool(
    name="weather_tool",
    description="Get current weather information for a city"
)
def get_weather(city: str) -> dict:
    \"\"\"Get weather data for a specific city.\"\"\"
    api_key = "your-weather-api-key"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"]
        }
    else:
        return {"error": "Could not fetch weather data"}

# Use in your agent config:
# tools:
#   weather_tool:
#     enabled: true
```

## Running the Example

```bash
cd examples/03_tool_usage
pip install -r requirements.txt
python tool_agent.py
```

## Key Benefits

### 🚀 **Extended Capabilities**
- Your agent can access real-world information
- Perform complex calculations accurately
- Work with files and data automatically

### 🔗 **Intelligent Tool Selection**
- Agent automatically chooses appropriate tools
- Combines multiple tools for complex tasks
- Explains its tool usage to users

### 🛡️ **Safe Execution**
- All tools run in sandboxed environments
- Input validation and output sanitization
- Configurable permissions and limits

### ⚡ **Easy Integration**
- No code changes required - just configuration
- Built-in tools work out of the box
- Custom tools integrate seamlessly

## Next Steps

1. **Try the tool agent**: Run the example and test different tool combinations
2. **Experiment with tool chaining**: Ask questions that require multiple tools
3. **Create custom tools**: Build tools for your specific domain
4. **Ready for memory?**: Check out [04_conversation_memory](../04_conversation_memory/)

## Key Concepts Learned

✅ **Tool Integration** via YAML configuration
✅ **Tool Chaining** for complex workflows
✅ **Safe Tool Execution** with built-in sandboxing
✅ **Custom Tool Creation** for domain-specific needs
✅ **Intelligent Tool Selection** by the agent

---

**🎉 Amazing!** Your agent now has superpowers! Tools transform Entity agents from simple chatbots into capable assistants that can interact with the real world.

*← Previous: [Agent Personality](../02_agent_personality/) | Next: [Conversation Memory](../04_conversation_memory/) →*
