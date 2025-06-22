from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.shared.react_step import ReActStep


@dataclass
class AgentResult:
    thread_id: str
    timestamp: datetime
    raw_input: str
    raw_output: str
    final_response: str
    tools_used: List[str]
    token_count: int
    memory_context: str
    intermediate_steps: List[Dict[str, Any]]
    react_steps: Optional[List[ReActStep]] = None  # Optional step trace
