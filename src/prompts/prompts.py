"""
Advanced Prompt Engineering Module for Agent Frameworks
Clean OOP design with polymorphism, dataclasses, and loose coupling
"""

import yaml
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Protocol
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import time

from src.prompts.models import (
    ExecutionContext,
    ExecutionResult,
    PromptConfiguration,
    PromptExample,
    PromptTechnique,
)


# ============================================================================
# Protocols and Interfaces
# ============================================================================


class LanguageModelInterface(Protocol):
    """Protocol for language model implementations"""

    async def generate_response(
        self, prompt: str, temperature: float = 0.7, max_tokens: Optional[int] = None
    ) -> str:
        """Generate response from language model"""
        ...


class TemplateEngineInterface(Protocol):
    """Protocol for template engines"""

    def render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        ...


class ValidationEngineInterface(Protocol):
    """Protocol for validation engines"""

    def validate_configuration(self, config: PromptConfiguration) -> bool:
        """Validate prompt configuration"""
        ...

    def validate_result(self, result: ExecutionResult) -> bool:
        """Validate execution result"""
        ...


# ============================================================================
# Core Abstractions
# ============================================================================


class PromptExecutor(ABC):
    """Abstract base for all prompt executors"""

    def __init__(self, configuration: PromptConfiguration):
        self.configuration = configuration
        self.technique_name = configuration.technique_name

    @abstractmethod
    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        language_model: LanguageModelInterface,
    ) -> ExecutionResult:
        """Execute the prompt technique"""
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        """Validate this executor's configuration"""
        pass

    def create_base_result(
        self,
        content: str,
        success: bool,
        execution_time: float,
        error: Optional[str] = None,
    ) -> ExecutionResult:
        """Helper to create standardized results"""
        return ExecutionResult(
            generated_content=content,
            technique_used=self.technique_name,
            execution_successful=success,
            execution_time_seconds=execution_time,
            error_message=error,
            metadata={"configuration": self.configuration.metadata},
        )


# ============================================================================
# Template Engine Implementation
# ============================================================================


class SimpleTemplateEngine:
    """Simple template engine for prompt formatting"""

    def render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variable substitution"""
        try:
            # Handle examples formatting
            if "examples" in variables and isinstance(variables["examples"], list):
                variables["examples"] = self._format_examples(variables["examples"])

            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

    def _format_examples(self, examples: List[PromptExample]) -> str:
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


# ============================================================================
# Validation Engine Implementation
# ============================================================================


class ConfigurationValidator:
    """Validates prompt configurations"""

    def validate_configuration(self, config: PromptConfiguration) -> bool:
        """Validate prompt configuration"""
        if not config.template:
            return False

        if "{query}" not in config.template:
            return False

        # Technique-specific validation
        if config.technique_name == PromptTechnique.FEW_SHOT:
            return len(config.examples) > 0

        if config.technique_name == PromptTechnique.PROMPT_CHAINING:
            return "chain_steps" in config.parameters

        return True

    def validate_result(self, result: ExecutionResult) -> bool:
        """Validate execution result"""
        return result.execution_successful and bool(result.generated_content)


# ============================================================================
# Concrete Prompt Executors
# ============================================================================


class ZeroShotExecutor(PromptExecutor):
    """Executes zero-shot prompting"""

    def __init__(
        self,
        configuration: PromptConfiguration,
        template_engine: TemplateEngineInterface,
    ):
        super().__init__(configuration)
        self.template_engine = template_engine

    def validate_configuration(self) -> bool:
        return bool(
            self.configuration.template and "{query}" in self.configuration.template
        )

    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        language_model: LanguageModelInterface,
    ) -> ExecutionResult:
        start_time = time.time()

        if not self.validate_configuration():
            return self.create_base_result(
                "", False, time.time() - start_time, "Invalid zero-shot configuration"
            )

        try:
            template_variables = {
                "query": execution_context.query,
                "system_message": self.configuration.system_message or "",
                **execution_context.additional_context,
                **self.configuration.parameters,
            }

            formatted_prompt = self.template_engine.render_template(
                self.configuration.template, template_variables
            )

            response = await language_model.generate_response(
                formatted_prompt,
                temperature=execution_context.temperature
                or self.configuration.temperature,
                max_tokens=execution_context.max_tokens,
            )

            execution_time = time.time() - start_time
            return self.create_base_result(response, True, execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            return self.create_base_result("", False, execution_time, str(e))


class FewShotExecutor(PromptExecutor):
    """Executes few-shot prompting with examples"""

    def __init__(
        self,
        configuration: PromptConfiguration,
        template_engine: TemplateEngineInterface,
    ):
        super().__init__(configuration)
        self.template_engine = template_engine

    def validate_configuration(self) -> bool:
        return (
            bool(
                self.configuration.template and "{query}" in self.configuration.template
            )
            and len(self.configuration.examples) > 0
        )

    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        language_model: LanguageModelInterface,
    ) -> ExecutionResult:
        start_time = time.time()

        if not self.validate_configuration():
            return self.create_base_result(
                "",
                False,
                time.time() - start_time,
                "Invalid few-shot configuration: examples required",
            )

        try:
            template_variables = {
                "query": execution_context.query,
                "examples": self.configuration.examples,
                "system_message": self.configuration.system_message or "",
                **execution_context.additional_context,
                **self.configuration.parameters,
            }

            formatted_prompt = self.template_engine.render_template(
                self.configuration.template, template_variables
            )

            response = await language_model.generate_response(
                formatted_prompt,
                temperature=execution_context.temperature
                or self.configuration.temperature,
                max_tokens=execution_context.max_tokens,
            )

            execution_time = time.time() - start_time
            return self.create_base_result(response, True, execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            return self.create_base_result("", False, execution_time, str(e))


class ChainOfThoughtExecutor(PromptExecutor):
    """Executes chain-of-thought prompting"""

    def __init__(
        self,
        configuration: PromptConfiguration,
        template_engine: TemplateEngineInterface,
    ):
        super().__init__(configuration)
        self.template_engine = template_engine

    def validate_configuration(self) -> bool:
        return bool(
            self.configuration.template and "{query}" in self.configuration.template
        )

    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        language_model: LanguageModelInterface,
    ) -> ExecutionResult:
        start_time = time.time()

        if not self.validate_configuration():
            return self.create_base_result(
                "",
                False,
                time.time() - start_time,
                "Invalid chain-of-thought configuration",
            )

        try:
            reasoning_instruction = self.configuration.parameters.get(
                "reasoning_instruction", "Let's think step by step:"
            )

            template_variables = {
                "query": execution_context.query,
                "reasoning_instruction": reasoning_instruction,
                "examples": self.configuration.examples,
                "system_message": self.configuration.system_message or "",
                **execution_context.additional_context,
                **self.configuration.parameters,
            }

            formatted_prompt = self.template_engine.render_template(
                self.configuration.template, template_variables
            )

            response = await language_model.generate_response(
                formatted_prompt,
                temperature=execution_context.temperature
                or self.configuration.temperature,
                max_tokens=execution_context.max_tokens,
            )

            execution_time = time.time() - start_time
            return self.create_base_result(response, True, execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            return self.create_base_result("", False, execution_time, str(e))


class SelfConsistencyExecutor(PromptExecutor):
    """Executes self-consistency prompting with multiple samples"""

    def __init__(
        self,
        configuration: PromptConfiguration,
        template_engine: TemplateEngineInterface,
    ):
        super().__init__(configuration)
        self.template_engine = template_engine

    def validate_configuration(self) -> bool:
        return bool(
            self.configuration.template and "{query}" in self.configuration.template
        )

    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        language_model: LanguageModelInterface,
    ) -> ExecutionResult:
        start_time = time.time()

        if not self.validate_configuration():
            return self.create_base_result(
                "",
                False,
                time.time() - start_time,
                "Invalid self-consistency configuration",
            )

        try:
            number_of_samples = self.configuration.parameters.get("num_samples", 3)

            template_variables = {
                "query": execution_context.query,
                "examples": self.configuration.examples,
                "system_message": self.configuration.system_message or "",
                **execution_context.additional_context,
                **self.configuration.parameters,
            }

            formatted_prompt = self.template_engine.render_template(
                self.configuration.template, template_variables
            )

            # Generate multiple responses
            all_responses = []
            for _ in range(number_of_samples):
                response = await language_model.generate_response(
                    formatted_prompt,
                    temperature=execution_context.temperature
                    or self.configuration.temperature,
                    max_tokens=execution_context.max_tokens,
                )
                all_responses.append(response)

            # Simple majority voting
            final_response = max(set(all_responses), key=all_responses.count)

            execution_time = time.time() - start_time
            result = self.create_base_result(final_response, True, execution_time)
            result.intermediate_steps = all_responses
            result.metadata.update(
                {"num_samples": number_of_samples, "all_responses": all_responses}
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            return self.create_base_result("", False, execution_time, str(e))


class PromptChainingExecutor(PromptExecutor):
    """Executes prompt chaining for multi-step reasoning"""

    def __init__(
        self,
        configuration: PromptConfiguration,
        template_engine: TemplateEngineInterface,
    ):
        super().__init__(configuration)
        self.template_engine = template_engine

    def validate_configuration(self) -> bool:
        return "chain_steps" in self.configuration.parameters

    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        language_model: LanguageModelInterface,
    ) -> ExecutionResult:
        start_time = time.time()

        if not self.validate_configuration():
            return self.create_base_result(
                "",
                False,
                time.time() - start_time,
                "Invalid chaining configuration: chain_steps required",
            )

        try:
            chain_steps_config = self.configuration.parameters["chain_steps"]
            current_input = execution_context.query
            intermediate_steps = []

            for step_config in chain_steps_config:
                step_template = step_config["template"]
                step_variables = {
                    "input": current_input,
                    "query": execution_context.query,
                    **execution_context.additional_context,
                    **step_config.get("parameters", {}),
                }

                formatted_step_prompt = self.template_engine.render_template(
                    step_template, step_variables
                )

                step_response = await language_model.generate_response(
                    formatted_step_prompt,
                    temperature=execution_context.temperature
                    or self.configuration.temperature,
                    max_tokens=execution_context.max_tokens,
                )

                step_name = step_config.get(
                    "name", f"Step {len(intermediate_steps) + 1}"
                )
                intermediate_steps.append(f"{step_name}: {step_response}")
                current_input = step_response

            execution_time = time.time() - start_time
            result = self.create_base_result(current_input, True, execution_time)
            result.intermediate_steps = intermediate_steps

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            return self.create_base_result("", False, execution_time, str(e))


class ReactExecutor(PromptExecutor):
    """Executes ReAct (Reasoning + Acting) prompting"""

    def __init__(
        self,
        configuration: PromptConfiguration,
        template_engine: TemplateEngineInterface,
    ):
        super().__init__(configuration)
        self.template_engine = template_engine

    def validate_configuration(self) -> bool:
        return bool(
            self.configuration.template and "{query}" in self.configuration.template
        )

    async def execute_prompt(
        self,
        execution_context: ExecutionContext,
        language_model: LanguageModelInterface,
    ) -> ExecutionResult:
        start_time = time.time()

        if not self.validate_configuration():
            return self.create_base_result(
                "", False, time.time() - start_time, "Invalid ReAct configuration"
            )

        try:
            react_format = self.configuration.parameters.get(
                "react_format",
                "Thought: [reasoning]\nAction: [action]\nObservation: [result]",
            )

            template_variables = {
                "query": execution_context.query,
                "react_format": react_format,
                "system_message": self.configuration.system_message or "",
                **execution_context.additional_context,
                **self.configuration.parameters,
            }

            formatted_prompt = self.template_engine.render_template(
                self.configuration.template, template_variables
            )

            response = await language_model.generate_response(
                formatted_prompt,
                temperature=execution_context.temperature
                or self.configuration.temperature,
                max_tokens=execution_context.max_tokens,
            )

            execution_time = time.time() - start_time
            return self.create_base_result(response, True, execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            return self.create_base_result("", False, execution_time, str(e))


# ============================================================================
# Factory for Executors
# ============================================================================


class PromptExecutorFactory:
    """Factory for creating prompt executors"""

    def __init__(self, template_engine: TemplateEngineInterface):
        self.template_engine = template_engine
        self._executor_registry = {
            PromptTechnique.ZERO_SHOT: ZeroShotExecutor,
            PromptTechnique.FEW_SHOT: FewShotExecutor,
            PromptTechnique.CHAIN_OF_THOUGHT: ChainOfThoughtExecutor,
            PromptTechnique.SELF_CONSISTENCY: SelfConsistencyExecutor,
            PromptTechnique.PROMPT_CHAINING: PromptChainingExecutor,
            PromptTechnique.REACT: ReactExecutor,
        }

    def create_executor(self, configuration: PromptConfiguration) -> PromptExecutor:
        """Create executor for given configuration"""
        executor_class = self._executor_registry.get(configuration.technique_name)
        if not executor_class:
            raise ValueError(f"Unsupported technique: {configuration.technique_name}")

        return executor_class(configuration, self.template_engine)

    def register_executor(self, technique: PromptTechnique, executor_class: type):
        """Register new executor type"""
        self._executor_registry[technique] = executor_class

    def get_supported_techniques(self) -> List[PromptTechnique]:
        """Get list of supported techniques"""
        return list(self._executor_registry.keys())


# ============================================================================
# Configuration Manager
# ============================================================================


class ConfigurationManager:
    """Manages prompt configurations from YAML"""

    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path
        self.configurations: Dict[PromptTechnique, PromptConfiguration] = {}

        if config_file_path:
            self.load_configurations()

    def load_configurations(self):
        """Load configurations from YAML file"""
        if not self.config_file_path or not Path(self.config_file_path).exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file_path}"
            )

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
                                explanation=example_data.get(
                                    "explanation", example_data.get("reasoning")
                                ),
                            )
                        )

                configuration = PromptConfiguration(
                    technique_name=prompt_technique,
                    template=technique_config.get("template", ""),
                    system_message=technique_config.get("system_message"),
                    examples=examples,
                    parameters=technique_config.get("parameters", {}),
                    validation_rules=technique_config.get("validation_rules", []),
                    max_retries=technique_config.get("max_retries", 3),
                    temperature=technique_config.get("temperature", 0.7),
                    timeout_seconds=technique_config.get("timeout_seconds", 30.0),
                    metadata=technique_config.get("metadata", {}),
                )

                self.configurations[prompt_technique] = configuration

            except ValueError as e:
                logging.warning(f"Unknown technique '{technique_name}' in config: {e}")

    def get_configuration(
        self, technique: PromptTechnique
    ) -> Optional[PromptConfiguration]:
        """Get configuration for specific technique"""
        return self.configurations.get(technique)

    def get_all_configurations(self) -> Dict[PromptTechnique, PromptConfiguration]:
        """Get all loaded configurations"""
        return self.configurations.copy()

    def add_configuration(self, configuration: PromptConfiguration):
        """Add new configuration"""
        self.configurations[configuration.technique_name] = configuration


# ============================================================================
# Main Orchestrator
# ============================================================================


class PromptOrchestrator:
    """Main orchestrator for prompt engineering operations"""

    def __init__(
        self,
        config_manager: ConfigurationManager,
        template_engine: Optional[TemplateEngineInterface] = None,
        validator: Optional[ValidationEngineInterface] = None,
    ):
        self.config_manager = config_manager
        self.template_engine = template_engine or SimpleTemplateEngine()
        self.validator = validator or ConfigurationValidator()

        self.executor_factory = PromptExecutorFactory(self.template_engine)
        self.executors: Dict[PromptTechnique, PromptExecutor] = {}

        self._initialize_executors()

    def _initialize_executors(self):
        """Initialize executors from configurations"""
        for technique, config in self.config_manager.get_all_configurations().items():
            if self.validator.validate_configuration(config):
                try:
                    executor = self.executor_factory.create_executor(config)
                    self.executors[technique] = executor
                except Exception as e:
                    logging.error(f"Failed to create executor for {technique}: {e}")
            else:
                logging.warning(f"Invalid configuration for {technique}")

    async def execute_technique(
        self,
        technique: PromptTechnique,
        query: str,
        language_model: LanguageModelInterface,
        additional_context: Optional[Dict[str, Any]] = None,
        **execution_kwargs,
    ) -> ExecutionResult:
        """Execute specific prompt technique"""
        if technique not in self.executors:
            return ExecutionResult(
                generated_content="",
                technique_used=technique,
                execution_successful=False,
                execution_time_seconds=0.0,
                error_message=f"Technique {technique.value} not available",
            )

        execution_context = ExecutionContext(
            query=query, additional_context=additional_context or {}, **execution_kwargs
        )

        executor = self.executors[technique]
        result = await executor.execute_prompt(execution_context, language_model)

        return result

    def get_available_techniques(self) -> List[PromptTechnique]:
        """Get list of available techniques"""
        return list(self.executors.keys())

    def add_custom_executor(
        self,
        technique: PromptTechnique,
        executor_class: type,
        configuration: PromptConfiguration,
    ):
        """Add custom executor"""
        self.executor_factory.register_executor(technique, executor_class)
        self.config_manager.add_configuration(configuration)

        if self.validator.validate_configuration(configuration):
            executor = self.executor_factory.create_executor(configuration)
            self.executors[technique] = executor


# ============================================================================
# Convenience Functions
# ============================================================================


def create_orchestrator_from_config(config_file_path: str) -> PromptOrchestrator:
    """Create orchestrator from configuration file"""
    config_manager = ConfigurationManager(config_file_path)
    return PromptOrchestrator(config_manager)


def create_simple_orchestrator() -> PromptOrchestrator:
    """Create orchestrator with minimal default configuration"""
    config_manager = ConfigurationManager()

    # Add basic zero-shot configuration
    basic_config = PromptConfiguration(
        technique_name=PromptTechnique.ZERO_SHOT,
        template="Please answer the following question: {query}",
    )
    config_manager.add_configuration(basic_config)

    return PromptOrchestrator(config_manager)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Mock language model for testing
    class MockLanguageModel:
        async def generate_response(
            self,
            prompt: str,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
        ) -> str:
            return f"Mock response to: {prompt[:50]}..."

    async def example_usage():
        # Create orchestrator
        orchestrator = create_simple_orchestrator()

        # Mock language model
        language_model = MockLanguageModel()

        # Execute technique
        result = await orchestrator.execute_technique(
            PromptTechnique.ZERO_SHOT, "What is the capital of France?", language_model
        )

        print(f"Result: {result.generated_content}")
        print(f"Success: {result.execution_successful}")
        print(f"Time: {result.execution_time_seconds:.2f}s")

    asyncio.run(example_usage())
