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
