from typing import Optional
from pydantic import BaseModel
from src.tools.tools import BaseToolPlugin


class FunFactInput(BaseModel):
    topic: Optional[str] = "space"


class FunFactTool(BaseToolPlugin):
    name = "fun_fact"
    description = "Tell a fun fact about a topic"
    args_schema = FunFactInput

    async def run(self, input_data: FunFactInput) -> str:
        return f"Did you know? {input_data.topic.capitalize()} is surprisingly cool."
