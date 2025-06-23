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
