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
