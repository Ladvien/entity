# plugins/fun_fact_tool.py

import logging
from typing import Dict
from pydantic import BaseModel, Field

from src.tools.base_tool_plugin import BaseToolPlugin

logger = logging.getLogger(__name__)


# -------------------------------
# 📥 Input Schema
# -------------------------------


class FunFactInput(BaseModel):
    topic: str = Field(
        default="space", description="The topic to return a sarcastic fun fact about"
    )


# -------------------------------
# 🎉 Fun Fact Tool
# -------------------------------


class FunFactTool(BaseToolPlugin):
    name = "fun_fact"
    description = "Returns a sarcastic fun fact"
    args_schema = FunFactInput

    def get_context_injection(
        self, user_input: str, thread_id: str = "default"
    ) -> Dict[str, str]:
        return {}  # No prompt injection needed

    async def run(self, input_data: FunFactInput) -> str:
        topic = input_data.topic.lower()

        facts = {
            "space": "Space is so empty, it's the perfect place to shout your problems into the void. Literally.",
            "ai": "AI will definitely steal your job—just as soon as it figures out how doors work.",
            "history": "History repeats itself, mostly because no one reads the footnotes.",
            "general": "Fun fact: The average person eats 3 spiders a year in their sleep. Or maybe that's just propaganda from spiders.",
        }

        return facts.get(
            topic, f"Fun fact about {topic}: It exists. Probably. ¯\\_(ツ)_/¯"
        )
