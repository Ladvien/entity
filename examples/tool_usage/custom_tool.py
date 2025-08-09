#!/usr/bin/env python3
"""Custom Tool Example - Build your own Entity plugins."""

import asyncio

from entity import Agent
from entity.defaults import load_defaults
from entity.plugins.tool import ToolPlugin
from entity.workflow.executor import WorkflowExecutor


class WordAnalyzer(ToolPlugin):
    """Custom tool that analyzes text statistics."""

    supported_stages = [WorkflowExecutor.DO]

    async def _execute_impl(self, context):
        text = context.message or ""

        # Perform analysis
        words = text.split()
        chars = len(text)
        sentences = text.count(".") + text.count("!") + text.count("?")

        return f"Words: {len(words)}, Characters: {chars}, Sentences: {sentences}"


class UppercaseTransformer(ToolPlugin):
    """Transform text to uppercase - simple but shows the pattern."""

    supported_stages = [WorkflowExecutor.REVIEW]  # Can run in REVIEW stage too!

    async def _execute_impl(self, context):
        return (context.message or "").upper()


async def main():
    """Agent with custom tool plugins."""

    resources = load_defaults()

    # Create instances of our custom tools
    analyzer = WordAnalyzer(resources)
    transformer = UppercaseTransformer(resources)

    # Build workflow with custom tools
    workflow = {
        "input": ["entity.cli.ent_cli_adapter.EntCLIAdapter"],
        "parse": ["entity.plugins.defaults.ParsePlugin"],
        "think": ["entity.plugins.defaults.ThinkPlugin"],
        "do": [analyzer],  # Our custom analyzer
        "review": [transformer],  # Our custom transformer
        "output": ["entity.cli.ent_cli_adapter.EntCLIAdapter"],
    }

    agent = Agent.from_workflow_dict(workflow, resources=resources)

    print("Text Analysis Agent with custom tools.")
    print("Type any text to analyze.\n")

    await agent.chat("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAnalysis complete.")
