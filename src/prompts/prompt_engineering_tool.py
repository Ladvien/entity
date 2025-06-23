# src/prompts/__init__.py
"""
Prompt Engineering Module for Entity Framework
Integrates with existing Entity architecture and ServiceRegistry
"""

from .orchestrator import PromptOrchestrator
from .models import PromptTechnique, ExecutionContext, ExecutionResult
from .config_manager import PromptConfigManager

__all__ = [
    "PromptOrchestrator",
    "PromptTechnique",
    "ExecutionContext",
    "ExecutionResult",
    "PromptConfigManager",
]

# src/prompts/models.py
"""
Data models for prompt engineering - integrates with Entity's existing patterns
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class PromptTechnique(Enum):
    """Available prompt engineering techniques"""

    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    SELF_CONSISTENCY = "self_consistency"
    PROMPT_CHAINING = "prompt_chaining"
    REACT = "react"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    GENERATE_KNOWLEDGE = "generate_knowledge"


@dataclass
class PromptExample:
    """Single example for few-shot learning"""

    input_text: str
    expected_output: str
    explanation: Optional[str] = None


@dataclass
class ExecutionContext:
    """Context for prompt execution - similar to Entity's ChatInteraction"""

    query: str
    thread_id: str = "default"
    additional_context: Dict[str, Any] = field(default_factory=dict)
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    use_memory: bool = True


@dataclass
class PromptConfiguration:
    """Configuration for a specific prompt technique"""

    technique_name: PromptTechnique
    template: str
    system_message: Optional[str] = None
    examples: List[PromptExample] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    temperature: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of prompt execution - similar to Entity's AgentResult"""

    generated_content: str
    technique_used: PromptTechnique
    execution_successful: bool
    execution_time_seconds: float
    thread_id: str
    timestamp: datetime
    token_count: Optional[int] = None
    confidence_score: Optional[float] = None
    intermediate_steps: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    memory_context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# src/prompts/config_manager.py
"""
Configuration manager for prompt techniques - integrates with Entity's config system
"""

import yaml
import logging
from typing import Dict, Optional
from pathlib import Path

from src.core.config import EntityServerConfig
from .models import PromptTechnique, PromptConfiguration, PromptExample

logger = logging.getLogger(__name__)


class PromptConfigManager:
    """Manages prompt configurations - integrates with Entity's config pattern"""

    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path
        self.configurations: Dict[PromptTechnique, PromptConfiguration] = {}

        if config_file_path:
            self.load_configurations()

    @classmethod
    def from_entity_config(
        cls, entity_config: EntityServerConfig
    ) -> "PromptConfigManager":
        """Create from Entity's main configuration"""
        # Look for prompt_engineering section in Entity config
        prompt_config_path = getattr(entity_config, "prompt_engineering_config", None)
        if prompt_config_path:
            return cls(prompt_config_path)

        # Create with defaults
        manager = cls()
        manager._load_defaults()
        return manager

    def load_configurations(self):
        """Load configurations from YAML file"""
        if not self.config_file_path or not Path(self.config_file_path).exists():
            logger.warning(
                f"Prompt config file not found: {self.config_file_path}, using defaults"
            )
            self._load_defaults()
            return

        try:
            with open(self.config_file_path, "r") as file:
                config_data = yaml.safe_load(file)

            techniques_config = config_data.get("techniques", {})

            for technique_name, technique_config in techniques_config.items():
                try:
                    prompt_technique = PromptTechnique(technique_name)

                    # Parse examples
                    examples = []
                    for example_data in technique_config.get("examples", []):
                        if isinstance(example_data, dict):
                            examples.append(
                                PromptExample(
                                    input_text=example_data.get(
                                        "question", example_data.get("input", "")
                                    ),
                                    expected_output=example_data.get(
                                        "answer", example_data.get("output", "")
                                    ),
                                    explanation=example_data.get("explanation"),
                                )
                            )

                    configuration = PromptConfiguration(
                        technique_name=prompt_technique,
                        template=technique_config.get("template", ""),
                        system_message=technique_config.get("system_message"),
                        examples=examples,
                        parameters=technique_config.get("parameters", {}),
                        temperature=technique_config.get("temperature", 0.7),
                        metadata=technique_config.get("metadata", {}),
                    )

                    self.configurations[prompt_technique] = configuration
                    logger.info(f"✅ Loaded prompt technique: {technique_name}")

                except ValueError as e:
                    logger.warning(f"Unknown technique '{technique_name}': {e}")

        except Exception as e:
            logger.error(f"Failed to load prompt configurations: {e}")
            self._load_defaults()

    def _load_defaults(self):
        """Load default configurations"""
        defaults = {
            PromptTechnique.ZERO_SHOT: PromptConfiguration(
                technique_name=PromptTechnique.ZERO_SHOT,
                template="{system_message}\n\nQuestion: {query}\n\nAnswer:",
                system_message="You are a helpful AI assistant.",
            ),
            PromptTechnique.CHAIN_OF_THOUGHT: PromptConfiguration(
                technique_name=PromptTechnique.CHAIN_OF_THOUGHT,
                template="{system_message}\n\nQuestion: {query}\n\n{reasoning_instruction}",
                system_message="You are a logical reasoning assistant.",
                parameters={"reasoning_instruction": "Let's think step by step:"},
            ),
            PromptTechnique.FEW_SHOT: PromptConfiguration(
                technique_name=PromptTechnique.FEW_SHOT,
                template="{system_message}\n\nExamples:\n{examples}\n\nQuestion: {query}\nAnswer:",
                system_message="You are a helpful AI assistant. Follow the examples provided.",
                examples=[
                    PromptExample("What is 2+2?", "2+2 equals 4"),
                    PromptExample(
                        "What is the capital of France?",
                        "The capital of France is Paris",
                    ),
                ],
            ),
        }

        self.configurations.update(defaults)
        logger.info(f"✅ Loaded {len(defaults)} default prompt configurations")

    def get_configuration(
        self, technique: PromptTechnique
    ) -> Optional[PromptConfiguration]:
        """Get configuration for specific technique"""
        return self.configurations.get(technique)

    def get_all_configurations(self) -> Dict[PromptTechnique, PromptConfiguration]:
        """Get all loaded configurations"""
        return self.configurations.copy()


# src/prompts/executors.py
"""
Prompt executors - integrates with Entity's LLM and memory systems
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Protocol

from langchain_core.language_models.base import BaseLanguageModel

from src.memory.memory_system import MemorySystem
from .models import (
    PromptConfiguration,
    ExecutionContext,
    ExecutionResult,
    PromptTechnique,
)

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Simple template engine for prompt formatting"""

    def render_template(self, template: str, variables: dict) -> str:
        """Render template with variable substitution"""
        try:
            # Handle examples formatting
            if "examples" in variables and isinstance(variables["examples"], list):
                variables["examples"] = self._format_examples(variables["examples"])

            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

    def _format_examples(self, examples) -> str:
        """Format examples for inclusion in templates"""
        if not examples:
            return ""

        formatted_examples = []
        for idx, example in enumerate(examples, 1):
            example_text = f"Example {idx}:\n"
            example_text += f"Input: {example.input_text}\n"
            example_text += f"Output: {example.expected_output}"
            if example.explanation:
                example_text += f"\nExplanation: {example.explanation}"
            formatted_examples.append(example_text)

        return "\n\n".join(formatted_examples)


class PromptExecutor(ABC):
    """Abstract base for all prompt executors"""

    def __init__(self, configuration: PromptConfiguration):
        self.configuration = configuration
        self.technique_name = configuration.technique_name
        self.template_engine = TemplateEngine()

    @abstractmethod
    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        llm: BaseLanguageModel,
        memory_system: MemorySystem = None,
    ) -> ExecutionResult:
        """Execute the prompt technique"""
        pass

    def create_base_result(
        self,
        content: str,
        success: bool,
        execution_time: float,
        context: ExecutionContext,
        error: str = None,
    ) -> ExecutionResult:
        """Helper to create standardized results"""
        return ExecutionResult(
            generated_content=content,
            technique_used=self.technique_name,
            execution_successful=success,
            execution_time_seconds=execution_time,
            thread_id=context.thread_id,
            timestamp=context.additional_context.get("timestamp", None),
            error_message=error,
            metadata={"configuration": self.configuration.metadata},
        )


class ZeroShotExecutor(PromptExecutor):
    """Executes zero-shot prompting"""

    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        llm: BaseLanguageModel,
        memory_system: MemorySystem = None,
    ) -> ExecutionResult:
        start_time = time.time()

        try:
            # Get memory context if requested
            memory_context = ""
            if execution_context.use_memory and memory_system:
                memories = await memory_system.search_memory(
                    execution_context.query, execution_context.thread_id, k=3
                )
                memory_context = "\n".join(doc.page_content for doc in memories)

            template_variables = {
                "query": execution_context.query,
                "system_message": self.configuration.system_message or "",
                "memory_context": memory_context,
                **execution_context.additional_context,
                **self.configuration.parameters,
            }

            formatted_prompt = self.template_engine.render_template(
                self.configuration.template, template_variables
            )

            response = await llm.ainvoke(formatted_prompt)

            execution_time = time.time() - start_time
            result = self.create_base_result(
                str(response), True, execution_time, execution_context
            )
            result.memory_context = memory_context

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Zero-shot execution failed: {e}")
            return self.create_base_result(
                "", False, execution_time, execution_context, str(e)
            )


class ChainOfThoughtExecutor(PromptExecutor):
    """Executes chain-of-thought prompting"""

    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        llm: BaseLanguageModel,
        memory_system: MemorySystem = None,
    ) -> ExecutionResult:
        start_time = time.time()

        try:
            # Get memory context if requested
            memory_context = ""
            if execution_context.use_memory and memory_system:
                memories = await memory_system.search_memory(
                    execution_context.query, execution_context.thread_id, k=3
                )
                memory_context = "\n".join(doc.page_content for doc in memories)

            reasoning_instruction = self.configuration.parameters.get(
                "reasoning_instruction", "Let's think step by step:"
            )

            template_variables = {
                "query": execution_context.query,
                "reasoning_instruction": reasoning_instruction,
                "examples": self.configuration.examples,
                "system_message": self.configuration.system_message or "",
                "memory_context": memory_context,
                **execution_context.additional_context,
                **self.configuration.parameters,
            }

            formatted_prompt = self.template_engine.render_template(
                self.configuration.template, template_variables
            )

            response = await llm.ainvoke(formatted_prompt)

            execution_time = time.time() - start_time
            result = self.create_base_result(
                str(response), True, execution_time, execution_context
            )
            result.memory_context = memory_context

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Chain-of-thought execution failed: {e}")
            return self.create_base_result(
                "", False, execution_time, execution_context, str(e)
            )


class SelfConsistencyExecutor(PromptExecutor):
    """Executes self-consistency prompting with multiple samples"""

    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        llm: BaseLanguageModel,
        memory_system: MemorySystem = None,
    ) -> ExecutionResult:
        start_time = time.time()

        try:
            # Get memory context if requested
            memory_context = ""
            if execution_context.use_memory and memory_system:
                memories = await memory_system.search_memory(
                    execution_context.query, execution_context.thread_id, k=3
                )
                memory_context = "\n".join(doc.page_content for doc in memories)

            number_of_samples = self.configuration.parameters.get("num_samples", 3)

            template_variables = {
                "query": execution_context.query,
                "examples": self.configuration.examples,
                "system_message": self.configuration.system_message or "",
                "memory_context": memory_context,
                **execution_context.additional_context,
                **self.configuration.parameters,
            }

            formatted_prompt = self.template_engine.render_template(
                self.configuration.template, template_variables
            )

            # Generate multiple responses
            all_responses = []
            for _ in range(number_of_samples):
                response = await llm.ainvoke(formatted_prompt)
                all_responses.append(str(response))

            # Simple majority voting
            final_response = max(set(all_responses), key=all_responses.count)

            execution_time = time.time() - start_time
            result = self.create_base_result(
                final_response, True, execution_time, execution_context
            )
            result.intermediate_steps = all_responses
            result.memory_context = memory_context
            result.metadata.update(
                {"num_samples": number_of_samples, "all_responses": all_responses}
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Self-consistency execution failed: {e}")
            return self.create_base_result(
                "", False, execution_time, execution_context, str(e)
            )


# src/prompts/orchestrator.py
"""
Main prompt orchestrator - integrates with Entity's ServiceRegistry
"""

import logging
from typing import Dict, List, Optional

from langchain_core.language_models.base import BaseLanguageModel

from src.core.registry import ServiceRegistry
from src.memory.memory_system import MemorySystem
from .models import PromptTechnique, ExecutionContext, ExecutionResult
from .config_manager import PromptConfigManager
from .executors import (
    PromptExecutor,
    ZeroShotExecutor,
    ChainOfThoughtExecutor,
    SelfConsistencyExecutor,
)

logger = logging.getLogger(__name__)


class PromptOrchestrator:
    """Main orchestrator for prompt engineering operations - integrates with Entity architecture"""

    def __init__(self, config_manager: PromptConfigManager):
        self.config_manager = config_manager
        self.executors: Dict[PromptTechnique, PromptExecutor] = {}

        # Executor registry
        self.executor_registry = {
            PromptTechnique.ZERO_SHOT: ZeroShotExecutor,
            PromptTechnique.CHAIN_OF_THOUGHT: ChainOfThoughtExecutor,
            PromptTechnique.SELF_CONSISTENCY: SelfConsistencyExecutor,
        }

        self._initialize_executors()

    @classmethod
    def from_service_registry(cls) -> "PromptOrchestrator":
        """Create orchestrator using Entity's ServiceRegistry"""
        try:
            config = ServiceRegistry.get("config")
            config_manager = PromptConfigManager.from_entity_config(config)
            return cls(config_manager)
        except Exception as e:
            logger.warning(f"Could not load from ServiceRegistry: {e}, using defaults")
            config_manager = PromptConfigManager()
            config_manager._load_defaults()
            return cls(config_manager)

    def _initialize_executors(self):
        """Initialize executors from configurations"""
        for technique, config in self.config_manager.get_all_configurations().items():
            if technique in self.executor_registry:
                try:
                    executor_class = self.executor_registry[technique]
                    executor = executor_class(config)
                    self.executors[technique] = executor
                    logger.debug(f"✅ Initialized executor for {technique.value}")
                except Exception as e:
                    logger.error(f"Failed to create executor for {technique}: {e}")

    async def execute_technique(
        self,
        technique: PromptTechnique,
        query: str,
        thread_id: str = "default",
        llm: BaseLanguageModel = None,
        memory_system: MemorySystem = None,
        use_memory: bool = True,
        **context_kwargs,
    ) -> ExecutionResult:
        """Execute specific prompt technique"""

        # Use ServiceRegistry if services not provided
        if llm is None:
            try:
                agent = ServiceRegistry.get("agent")
                llm = agent.llm
            except:
                raise ValueError("No LLM provided and none found in ServiceRegistry")

        if memory_system is None and use_memory:
            try:
                memory_system = ServiceRegistry.get("memory")
            except:
                logger.warning("No memory system found in ServiceRegistry")
                use_memory = False

        if technique not in self.executors:
            return ExecutionResult(
                generated_content="",
                technique_used=technique,
                execution_successful=False,
                execution_time_seconds=0.0,
                thread_id=thread_id,
                timestamp=None,
                error_message=f"Technique {technique.value} not available",
            )

        execution_context = ExecutionContext(
            query=query,
            thread_id=thread_id,
            use_memory=use_memory,
            additional_context=context_kwargs,
        )

        executor = self.executors[technique]
        result = await executor.execute_prompt(execution_context, llm, memory_system)

        return result

    def get_available_techniques(self) -> List[PromptTechnique]:
        """Get list of available techniques"""
        return list(self.executors.keys())

    def register_custom_executor(
        self, technique: PromptTechnique, executor_class: type
    ):
        """Register custom executor"""
        self.executor_registry[technique] = executor_class

        # Reinitialize if config exists
        config = self.config_manager.get_configuration(technique)
        if config:
            self.executors[technique] = executor_class(config)


# src/plugins/prompt_engineering_tool.py
"""
Prompt engineering tool plugin for Entity framework
"""

import logging
from typing import Dict, Any
from pydantic import BaseModel, Field

from src.plugins.base import BaseToolPlugin
from src.core.registry import ServiceRegistry
from src.prompts.orchestrator import PromptOrchestrator
from src.prompts.models import PromptTechnique

logger = logging.getLogger(__name__)


class PromptEngineeringArgs(BaseModel):
    """Arguments for prompt engineering tool"""

    technique: str = Field(
        description="Prompt technique to use (zero_shot, chain_of_thought, self_consistency)"
    )
    query: str = Field(description="The query to process with the technique")
    use_memory: bool = Field(default=True, description="Whether to use memory context")


class PromptEngineeringTool(BaseToolPlugin):
    """Tool for applying advanced prompt engineering techniques"""

    name = "prompt_engineering"
    description = "Apply advanced prompt engineering techniques like chain-of-thought or self-consistency to queries"
    args_schema = PromptEngineeringArgs

    def __init__(self):
        self.orchestrator = None

    async def run(self, input_data: PromptEngineeringArgs) -> str:
        """Execute prompt engineering technique"""
        try:
            # Initialize orchestrator if needed
            if self.orchestrator is None:
                self.orchestrator = PromptOrchestrator.from_service_registry()

            # Parse technique
            try:
                technique = PromptTechnique(input_data.technique.lower())
            except ValueError:
                available = [
                    t.value for t in self.orchestrator.get_available_techniques()
                ]
                return f"Unknown technique '{input_data.technique}'. Available: {', '.join(available)}"

            # Get current thread context from ServiceRegistry if available
            thread_id = "default"
            try:
                # This would come from current conversation context
                # You might want to pass this through the tool execution context
                pass
            except:
                pass

            # Execute technique
            result = await self.orchestrator.execute_technique(
                technique=technique,
                query=input_data.query,
                thread_id=thread_id,
                use_memory=input_data.use_memory,
            )

            if result.execution_successful:
                response = f"**{technique.value.replace('_', ' ').title()} Result:**\n\n{result.generated_content}"

                if result.intermediate_steps:
                    response += f"\n\n**Reasoning Steps:** {len(result.intermediate_steps)} steps completed"

                if result.memory_context:
                    response += "\n\n*Used memory context from previous conversations*"

                return response
            else:
                return f"Prompt engineering failed: {result.error_message}"

        except Exception as e:
            logger.error(f"Prompt engineering tool failed: {e}")
            return f"Error executing prompt technique: {str(e)}"

    def get_context_injection(
        self, user_input: str, thread_id: str = "default"
    ) -> Dict[str, Any]:
        """No additional context injection needed"""
        return {}
