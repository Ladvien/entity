from __future__ import annotations

from entity.core.plugins import PromptPlugin, ValidationResult
from entity.core.context import PluginContext
from pipeline.stages import PipelineStage


class IntentClassifierPrompt(PromptPlugin):
    """Classify user intent using an LLM.

    Uses **Structured LLM Access (22)** so prompt logic stays simple
    while maintaining observability.
    """

    dependencies = ["llm"]
    stages = [PipelineStage.THINK]

    @classmethod
    def validate_config(cls, config: dict) -> ValidationResult:
        if "confidence_threshold" not in config:
            return ValidationResult.error_result("missing confidence_threshold")
        try:
            value = float(config["confidence_threshold"])
        except (TypeError, ValueError):
            return ValidationResult.error_result(
                "confidence_threshold must be a number"
            )
        if not 0.0 <= value <= 1.0:
            return ValidationResult.error_result(
                "confidence_threshold must be between 0 and 1"
            )
        return ValidationResult.success_result()

    async def _execute_impl(self, context: PluginContext) -> None:
        last_message = context.conversation()[-1].content
        prompt = "Classify the user's intent in one word.\n" f"Message: {last_message}"
        response = await self.call_llm(context, prompt, purpose="intent_classification")
        context.cache("intent", response.content)
