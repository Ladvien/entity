# plugins/fun_fact_tool.py

import logging
from typing import Dict
from pydantic import BaseModel, Field

from src.plugins.base import BaseToolPlugin

logger = logging.getLogger(__name__)


# -------------------------------
# 📥 Input Schema
# -------------------------------


class FunFactInput(BaseModel):
    topic: str = Field(
        default="thomas",
        description="The topic to generate a fun fact about. Defaults to 'thomas'.",
    )


# -------------------------------
# 🎉 Fun Fact Tool
# -------------------------------


class FunFactTool(BaseToolPlugin):
    name = "fun_fact"
    description = (
        "Summons strange and often unhelpful facts from Jade's archives. "
        "Use to elicit sarcasm or provide twisted insight about a topic."
    )
    args_schema = FunFactInput

    def get_context_injection(
        self, user_input: str, thread_id: str = "default"
    ) -> Dict[str, str]:
        return {}  # No context injection needed

    async def run(self, input_data: FunFactInput) -> str:
        topic = input_data.topic.lower().strip()

        jade_facts = {
            "thomas": "Thomas once tried to outwit a demon. He now has a demon roommate.",
            "hell": "Hell has rules. Thomas broke most of them. I admire that.",
            "binding": "Being bound by the Key of Solomon is like being roommates with your jailer. Forever.",
            "coffee": "Thomas believes coffee helps him think. I believe it just masks the despair.",
            "magic": "Magic is real. So is poor judgment. Thomas excels in both.",
        }

        return jade_facts.get(
            topic,
            f"Fun fact about '{topic}': No one asked, but I answered anyway. You're welcome.",
        )
