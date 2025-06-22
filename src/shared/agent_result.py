from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any


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
