from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, List

from ..state import PipelineState


@dataclass
class StateManagerMetrics:
    """Simple metrics collected by :class:`StateManager`."""

    states_saved: int = 0
    states_loaded: int = 0
    states_evicted: int = 0


class StateManager:
    """Persist pipeline states with a fixed maximum size."""

    def __init__(self, max_states: int = 100) -> None:
        self._max_states = max_states
        self._states: Dict[str, PipelineState] = {}
        self._order: List[str] = []
        self.metrics = StateManagerMetrics()
        self._lock = asyncio.Lock()

    async def save_state(self, state: PipelineState) -> None:
        """Store a snapshot of ``state`` and enforce the size limit."""

        async with self._lock:
            snapshot = state.snapshot()
            pipeline_id = snapshot.pipeline_id
            self._states[pipeline_id] = snapshot
            if pipeline_id in self._order:
                self._order.remove(pipeline_id)
            self._order.append(pipeline_id)
            self.metrics.states_saved += 1
            if len(self._order) > self._max_states:
                oldest = self._order.pop(0)
                if oldest in self._states:
                    del self._states[oldest]
                    self.metrics.states_evicted += 1

    async def load_state(self, pipeline_id: str) -> PipelineState | None:
        """Retrieve a saved state by ``pipeline_id``."""

        async with self._lock:
            state = self._states.get(pipeline_id)
            if state is not None:
                self.metrics.states_loaded += 1
                return state.snapshot()
            return None

    async def pipeline_ids(self) -> List[str]:
        async with self._lock:
            return list(self._order)

    async def count(self) -> int:
        async with self._lock:
            return len(self._states)
