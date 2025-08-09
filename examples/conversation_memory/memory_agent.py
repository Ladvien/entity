#!/usr/bin/env python3
"""Memory Agent - Demonstrates Entity's persistent memory system."""

import asyncio

from entity import Agent
from entity.defaults import load_defaults
from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class MemoryPlugin(Plugin):
    """Plugin that remembers and recalls information."""

    supported_stages = [WorkflowExecutor.THINK]
    dependencies = ["memory"]

    async def _execute_impl(self, context):
        message = context.message or ""

        # Handle remember commands
        if message.startswith("remember "):
            fact = message[9:]
            await context.remember("user_facts", fact)
            return f"I'll remember: {fact}"

        # Handle recall commands
        if message.startswith("what do you remember"):
            facts = await context.recall("user_facts", "Nothing yet")
            return f"I remember: {facts}"

        # Track conversation count
        count = await context.recall("msg_count", 0)
        await context.remember("msg_count", count + 1)

        return f"Message #{count + 1}: {message}"


async def main():
    """Agent with persistent memory capabilities."""

    resources = load_defaults()

    # Create memory-aware workflow
    workflow = {
        "input": ["entity.cli.ent_cli_adapter.EntCLIAdapter"],
        "parse": ["entity.plugins.defaults.ParsePlugin"],
        "think": [MemoryPlugin(resources)],  # Custom memory handler
        "do": ["entity.plugins.defaults.DoPlugin"],
        "review": ["entity.plugins.defaults.ReviewPlugin"],
        "output": ["entity.cli.ent_cli_adapter.EntCLIAdapter"],
    }

    agent = Agent.from_workflow_dict(workflow, resources=resources)

    print("Memory Agent - I remember across sessions!")
    print("Commands: 'remember [fact]', 'what do you remember'\n")

    await agent.chat("", user_id="demo_user")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMemory saved. See you next time!")
