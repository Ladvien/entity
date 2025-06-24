from src.core.config import EntityServerConfig
from src.plugins.prompts.plugin import PromptPlugin
from src.plugins.prompts.validation import ValidationResult
from src.plugins.registry import ToolManager
from src.server.agent import EntityAgent

# NEW: Import prompt plugin system
from src.plugins.prompts.manager import PromptPluginManager
from src.plugins.prompts.context import PromptContext

import asyncio
import yaml
from rich import print
from langchain_ollama import OllamaLLM
from src.memory.memory_system import MemorySystem


from typing import Set


class ChainOfThoughtPlugin(PromptPlugin):
    """Chain-of-Thought prompting strategy"""

    def __init__(self, config=None):
        super().__init__(config)
        self.name = "chain_of_thought"

    def generate_prompt(self, context: PromptContext) -> str:
        """Generate Chain-of-Thought prompt"""
        personality = context.get_personality_vars()

        return """You are a thoughtful AI assistant that thinks step-by-step before answering.

For each question, follow this process:
1. **Understanding**: Break down what the question is asking
2. **Analysis**: Think through the problem step by step
3. **Reasoning**: Show your work and logical progression
4. **Verification**: Double-check your reasoning
5. **Conclusion**: Provide the final answer

Question: {input}

Let me think through this step by step:

{agent_scratchpad}"""

    def validate_prompt(self) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        result.add_info("Chain-of-Thought", "Using step-by-step reasoning approach")
        return result

    def get_required_variables(self) -> Set[str]:
        return {"input", "agent_scratchpad"}


# ──────────────────────────────────────────────────────────────────────────────
# Updated YAML config with prompt plugin configuration
# ──────────────────────────────────────────────────────────────────────────────

config_yaml = """
ollama:
  base_url: "http://192.168.1.110:11434"
  model: "llama3:8b-instruct-q6_K"
  temperature: 0.7
  top_p: 0.9
  top_k: 40
  repeat_penalty: 1.1

data:
  host: "192.168.1.104"
  port: 5432
  name: "memory"
  username: "${DB_USERNAME}"
  password: "${DB_PASSWORD}"
  db_schema: "entity"
  history_table: "chat_history"
  min_pool_size: 2
  max_pool_size: 10
  init_on_startup: true

# 🔥 TTS Configuration for speech server integration
tts:
  base_url: "http://192.168.1.110:8888"  # Your speech server URL
  voice_name: "bf_emma"
  voice_sample_path: "voice_samples/ai_mee.wav"
  output_format: "wav"
  speed: 0.3
  cfg_weight: 0.9
  exaggeration: 0.5
  # Audio settings
  sample_rates: [44100, 48000, 22050, 16000, 8000]
  fade_out_samples: 2000

memory:
  collection_name: "entity_memory"
  embedding_model: "all-MiniLM-L6-v2"
  embedding_dimension: 384
  max_context_length: 1000
  similarity_threshold: 0.3
  memory_limit: 50
  pruning_enabled: true
  pruning_days: 90
  keep_important_threshold: 0.7
  min_access_count: 2

tools:
  plugin_path: "./plugins_user/plugins"
  enabled: []

entity:
  entity_id: "jade"
  max_iterations: 500
  name: "Jade"
  
  # Personality settings
  sarcasm_level: 0.8
  loyalty_level: 0.6
  anger_level: 0.7
  wit_level: 0.9
  response_brevity: 0.7
  memory_influence: 0.8
  
  # ONLY CHANGE: Updated prompt section for plugin system
  prompt:
    plugin: "chain_of_thought"    # Use CoT plugin instead of ReAct
    template: "analytical"        # Specific template for detailed reasoning
    fallback: "react"            # Fallback to ReAct if CoT fails
    
    # Strategy-specific settings
    strategy_settings:
      reasoning_depth: "detailed"    # How thorough the reasoning should be
      show_work: true               # Show step-by-step calculations
      verify_logic: true            # Double-check reasoning steps
      max_reasoning_steps: 5        # Max steps before conclusion

server:
  host: "0.0.0.0"
  port: 8000
  reload: false
  log_level: "info"

logging:
  level: "DEBUG"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_enabled: true
  file_path: "logs/entity.log"
  max_file_size: 10485760
  backup_count: 5

adapters:
  - type: tts
    enabled: true
    settings:
      voice_name: "bf_emma"  # Override if needed
      speed: 0.3  # Override if needed
"""

# ──────────────────────────────────────────────────────────────────────────────
# Test prompts for different reasoning scenarios
# ──────────────────────────────────────────────────────────────────────────────

test_prompts = """
# Simple math problem
simple_math:
  input: "If Alice has 3 apples and gives 1 to Bob, how many does she have left?"
  expected_output:
    contains: "2"
    reasoning_required: true

# Multi-step reasoning
complex_reasoning:
  input: "A train leaves station A at 2 PM traveling at 60 mph. Another train leaves station B (120 miles away) at 2:30 PM traveling toward station A at 80 mph. When do they meet?"
  expected_output:
    contains: "3:12 PM"
    reasoning_required: true

# Logic puzzle
logic_puzzle:
  input: "If all roses are flowers, and some flowers are red, can we conclude that some roses are red?"
  expected_output:
    contains: "cannot conclude" 
    reasoning_required: true

# Word problem
word_problem:
  input: "Sarah bought 4 boxes of cookies. Each box contains 12 cookies. She ate 5 cookies and gave away 2 boxes to friends. How many cookies does she have left?"
  expected_output:
    contains: "19"
    reasoning_required: true
"""

# ──────────────────────────────────────────────────────────────────────────────


async def main():
    print(
        "[bold cyan]🔧 Initializing Chain-of-Thought example with plugin system...[/]"
    )

    # Load configuration
    config = EntityServerConfig.config_from_str(config_yaml)
    test_data = yaml.safe_load(test_prompts)

    print("[bold blue]🧩 Setting up prompt plugin system...[/]")

    # Initialize prompt plugin manager
    prompt_manager = PromptPluginManager()

    # Register our inline plugin
    prompt_manager.register_plugin("chain_of_thought", ChainOfThoughtPlugin)
    print("✅ Registered Chain-of-Thought plugin")

    # Auto-discover plugins from directory (optional)
    try:
        discovered = prompt_manager.auto_discover_plugins(
            "src/plugins/prompts/strategies"
        )
        if discovered:
            print(f"✅ Discovered additional plugins: {discovered}")
        else:
            print("ℹ️ No additional plugins found in strategies directory")
    except Exception as e:
        print(f"ℹ️ Plugin discovery: {e}")

    # Get the configured prompt plugin
    plugin_name = config.entity.prompt.plugin
    try:
        prompt_plugin = prompt_manager.get_plugin(plugin_name)
        print(f"✅ Loaded prompt plugin: {plugin_name}")
    except Exception as e:
        print(f"❌ Failed to load plugin '{plugin_name}': {e}")
        raise RuntimeError(f"Required plugin '{plugin_name}' not available")

    # Validate the prompt plugin
    print("[bold yellow]🔍 Validating prompt configuration...[/]")
    validation_result = prompt_plugin.validate_prompt()

    if validation_result.is_valid:
        print("✅ Prompt validation passed!")
    else:
        print("⚠️ Prompt validation issues found:")
        for issue in validation_result.issues:
            print(f"  - {issue.category}: {issue.message}")

    # Initialize components
    print("[bold cyan]⚙️ Initializing agent components...[/]")

    # Initialize tool manager (needed for prompt context)
    tools = ToolManager(config.tools)

    # Generate dynamic prompt using the plugin
    print("[bold magenta]🎭 Generating dynamic prompt...[/]")
    prompt_context = PromptContext(
        personality=config.entity,
        tools=tools.get_all_tools(),
        memory_config=config.memory,
        custom_variables={"reasoning_mode": "detailed", "show_work": True},
    )

    try:
        generated_prompt = prompt_plugin.generate_prompt(prompt_context)
        print("✅ Dynamic prompt generated successfully")
        print(f"[dim]Preview: {generated_prompt[:200]}...[/]")
    except Exception as e:
        print(f"❌ Prompt generation failed: {e}")
        raise RuntimeError(f"Prompt generation failed: {e}")

    # Initialize LLM with generated prompt
    llm = OllamaLLM(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        top_p=config.ollama.top_p,
        top_k=config.ollama.top_k,
        repeat_penalty=config.ollama.repeat_penalty,
        base_template=generated_prompt.strip(),
    )

    # Create a mock memory system for this example (no database needed)
    class MockMemorySystem:
        def __init__(self, *args, **kwargs):
            pass

        async def initialize(self):
            print("✅ Mock memory system initialized")

        async def close(self):
            pass

    memory = MockMemorySystem()

    # Initialize agent with prompt plugin
    agent = EntityAgent(
        config=config.entity,
        llm=llm,
        memory_system=memory,
        tool_manager=tools,
        output_adapter_manager=None,
        prompt_plugin=prompt_plugin,  # Pass the prompt plugin
    )
    await agent.initialize()

    print("\n[bold yellow]▶ Running Chain-of-Thought Examples[/]")
    print("=" * 60)

    # Test each prompt scenario
    for test_name, test_case in test_data.items():
        print(f"\n[bold cyan]🧮 Test: {test_name.replace('_', ' ').title()}[/]")
        print(f"[dim]Question: {test_case['input']}[/]")
        print("-" * 40)

        try:
            # Run the test
            result = await agent.chat(test_case["input"], thread_id=f"cot-{test_name}")

            print(f"\n[bold green]🧠 Agent Response:[/]")
            print(result.final_response)

            # Check if expected output is present
            expected = test_case.get("expected_output", {})
            if expected.get("contains"):
                if expected["contains"] in result.final_response:
                    print(
                        f"[green]✅ Expected content found: '{expected['contains']}'[/]"
                    )
                else:
                    print(
                        f"[red]❌ Expected content missing: '{expected['contains']}'[/]"
                    )

            # Check if reasoning was shown (for CoT evaluation)
            if expected.get("reasoning_required"):
                reasoning_indicators = [
                    "step",
                    "because",
                    "therefore",
                    "first",
                    "next",
                    "then",
                ]
                has_reasoning = any(
                    indicator in result.final_response.lower()
                    for indicator in reasoning_indicators
                )
                if has_reasoning:
                    print("[green]✅ Reasoning steps detected[/]")
                else:
                    print("[yellow]⚠️ Limited reasoning steps shown[/]")

        except Exception as e:
            print(f"[red]❌ Test failed with error: {e}[/]")

        print("=" * 60)

    # Plugin performance summary
    print(f"\n[bold magenta]📊 Plugin Performance Summary[/]")
    print(f"Plugin used: {plugin_name}")
    print(
        f"Validation status: {'✅ Passed' if validation_result.is_valid else '⚠️ Issues found'}"
    )
    print(f"Prompt generation: ✅ Success")

    await memory.close()
    print("\n[bold green]🎉 Chain-of-Thought example completed![/]")


if __name__ == "__main__":
    asyncio.run(main())
