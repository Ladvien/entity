# plugins/fun_fact_tool.py

from typing import Optional
from pydantic import BaseModel
import logging

from src.tools.tools import BaseToolPlugin

logger = logging.getLogger(__name__)


class FunFactInput(BaseModel):
    topic: Optional[str] = "space"


class FunFactTool(BaseToolPlugin):
    name = "fun_fact"
    description = "Returns a fun fact about a given topic."
    args_schema = FunFactInput

    async def run(self, input_data: FunFactInput) -> str:
        try:
            topic = input_data.topic or "space"
            return f"Did you know that {topic.capitalize()} is fascinating?"
        except Exception as e:
            logger.exception("FunFactTool failed")
            return f"[Error] {str(e)}"
