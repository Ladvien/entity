"""
Example: React
Description: Uses a tool and stops with a final answer.
"""

import asyncio
import yaml
from rich import print

from src.memory.memory_system import MemorySystem
from src.plugins.registry import ToolManager
from src.adapters import create_output_adapters
from src.service.agent import EntityAgent

# Embedded YAML-style prompt configuration
example_yaml = """agent_scratchpad: I should use the fun_fact tool.
expected_output:
  contains: Final Answer
input: Tell me a fun fact.
memory_context: ''
step_count: 1
tool_names:
- fun_fact
tool_used: fun_fact
tools: 'fun_fact: returns a random fun fact'"""
example = yaml.safe_load(example_yaml)


async def main():
    memory = MemorySystem(config=config)
    tools = ToolManager(config=config)
    output_adapters = create_output_adapters(config)
    agent = EntityAgent(config=config, memory_system=memory, tool_manager=tools, output_adapters=output_adapters)

    print("[bold yellow]▶ Running example:[/] react")
    response = await agent.run(example["input"], thread_id="example-thread", variables=example)

    print("\n[bold green]🧠 Agent Response:[/]")
    print(response)

    expected = example.get("expected_output", {})
    if expected.get("contains") and expected["contains"] not in response:
        print(f"[red]❌ Expected to contain:[/] {expected['contains']}")
    else:
        print("[green]✅ Output matched expectation[/]")

if __name__ == "__main__":
    asyncio.run(main())