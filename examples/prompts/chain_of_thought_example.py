"""
Example: Chain Of Thought
Description: Demonstrates reasoning before the final answer using advanced prompting.
"""

import asyncio
import yaml
from rich import print
from langchain_ollama import OllamaLLM

from src.core.config import EntityServerConfig
from src.memory.memory_system import MemorySystem
from src.plugins.registry import ToolManager
from src.server.routes.agent import EntityAgent

# ──────────────────────────────────────────────────────────────────────────────
# Embedded YAML config (top-level keys only) – no 'data:' wrapper required
# ──────────────────────────────────────────────────────────────────────────────
config_yaml = """
ollama:
  base_url: "http://localhost:11434"
  model: "llama3:8b-instruct-q6_K"
  temperature: 0.7
  top_p: 0.9
  top_k: 40
  repeat_penalty: 1.1

database:
  host: "localhost"
  port: 5432
  name: "memory"
  username: "test_user"        # 💡 Replace with your actual DB username
  password: "test_pass"        # 💡 Replace with your actual DB password
  db_schema: "entity"

memory:
  collection_name: "entity_memory"
  embedding_model: "all-MiniLM-L6-v2"
  embedding_dimension: 384

tools:
  plugin_path: "./plugins_user/plugins"
  enabled: []

tts:
  enabled: false

entity:
  entity_id: "test"
  max_iterations: 3
  name: "TestAgent"
  enable_advanced_prompting: true   # ✅ Required for Chain-of-Thought prompting

server:
  host: "0.0.0.0"
  port: 8000
  reload: false
  log_level: "info"

logging:
  level: "WARNING"
  format: "%(asctime)s - %(levelname)s - %(message)s"
  file_enabled: false
  file_path: "logs/test.log"
  max_file_size: 1048576
  backup_count: 2
"""

# ──────────────────────────────────────────────────────────────────────────────
# Prompt test block (separated from config)
# ──────────────────────────────────────────────────────────────────────────────
prompt_yaml = """
input: If Alice has 3 apples and gives 1 to Bob, how many does she have left?
expected_output:
  contains: "2"
"""

# ──────────────────────────────────────────────────────────────────────────────


async def main():
    print("[bold cyan]🔧 Initializing config and components...[/]")

    config = EntityServerConfig.config_from_str(config_yaml)
    prompt_data = yaml.safe_load(prompt_yaml)

    # LLM setup
    llm = OllamaLLM(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        top_p=config.ollama.top_p,
        top_k=config.ollama.top_k,
        repeat_penalty=config.ollama.repeat_penalty,
    )

    memory = MemorySystem(config.memory, config.database_config)
    tools = ToolManager(config=config)

    agent = EntityAgent(
        config=config,
        llm=llm,
        memory_system=memory,
        tool_manager=tools,
        output_adapter_manager=None,
    )

    await agent.initialize()

    print("[bold yellow]▶ Running Chain-of-Thought Prompt Example[/]")
    result = await agent.chat(prompt_data["input"], thread_id="example-thread")

    print("\n[bold green]🧠 Agent Response:[/]")
    print(result.final_response)

    expected = prompt_data.get("expected_output", {})
    if expected.get("contains") and expected["contains"] not in result.final_response:
        print(f"[red]❌ Expected output to contain:[/] '{expected['contains']}'")
    else:
        print("[green]✅ Output matched expectation[/]")


if __name__ == "__main__":
    asyncio.run(main())
