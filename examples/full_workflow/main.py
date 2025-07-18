import asyncio
import os
import sys
from pathlib import Path

# Ensure this example can find the entity package when run directly
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from entity.core.agent import Agent
from entity.core.registries import SystemRegistries
from entity.core.agent import AgentRuntime
from entity.core.stages import PipelineStage
from entity.resources.llm import LLM
from entity.resources.memory import Memory
from entity.resources.storage import Storage
from entity.resources.logging import LoggingResource
from entity.resources.metrics import MetricsCollectorResource
from entity.infrastructure.postgres import PostgresInfrastructure
from entity.resources.interfaces.postgres_resource import PostgresResource
from plugins.builtin.resources import OllamaLLMResource, PgVectorStore
from plugins.builtin.basic_error_handler import BasicErrorHandler
from examples.plugins import InputLogger, MessageParser, ResponseReviewer

from .providers import AnthropicLLMResource, OpenAILLMResource
from .plugins import MultiProviderResponder, VectorStoreLogger
from entity.workflows.base import Workflow


class FullWorkflow(Workflow):
    """Route the message through all custom plugins."""

    stage_map = {
        PipelineStage.INPUT: ["InputLogger"],
        PipelineStage.PARSE: ["MessageParser"],
        PipelineStage.THINK: ["multi_responder"],
        PipelineStage.REVIEW: ["vector_logger", "ResponseReviewer"],
        PipelineStage.ERROR: ["basic_error_handler"],
    }


async def build_agent() -> Agent:
    agent = Agent(workflow=FullWorkflow())
    builder = agent.builder

    # Register resources
    builder.resource_registry.register(
        "database_backend",
        PostgresInfrastructure,
        {
            "dsn": os.getenv(
                "POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/postgres"
            )
        },
    )
    builder.resource_registry.register("database", PostgresResource, {})
    builder.resource_registry.register(
        "vector_store", PgVectorStore, {"table": "embeddings", "dimensions": 256}
    )
    builder.resource_registry.register("memory", Memory, {})
    builder.resource_registry.register(
        "llm_provider",
        OllamaLLMResource,
        {
            "model": os.getenv("OLLAMA_MODEL", "llama3"),
            "base_url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
        },
    )
    builder.resource_registry.register(
        "openai_provider",
        OpenAILLMResource,
        {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
        },
    )
    builder.resource_registry.register(
        "anthropic_provider",
        AnthropicLLMResource,
        {
            "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        },
    )
    builder.resource_registry.register("llm", LLM, {})
    builder.resource_registry.register("storage", Storage, {})
    builder.resource_registry.register(
        "logging", LoggingResource, {"outputs": [{"type": "console"}]}
    )
    builder.resource_registry.register(
        "metrics_collector", MetricsCollectorResource, {}
    )

    # Register plugins
    await builder.add_plugin(InputLogger({}))
    await builder.add_plugin(MessageParser({}))
    await builder.add_plugin(ResponseReviewer({}))
    await builder.add_plugin(BasicErrorHandler({}))
    await builder.add_plugin(MultiProviderResponder({}))
    await builder.add_plugin(VectorStoreLogger({}))

    runtime = await builder.build_runtime(workflow=agent.workflow)
    agent._runtime = runtime
    return agent


async def main() -> None:
    agent = await build_agent()
    result = await agent.handle("Explain the Eiffel Tower")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
