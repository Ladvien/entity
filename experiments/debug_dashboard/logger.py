"""State transition logging and replay utilities."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator, Iterable

from pipeline.state import PipelineState
from pipeline.stages import PipelineStage


@dataclass
class StateTransition:
    """Recorded pipeline state at a specific stage."""

    timestamp: str
    pipeline_id: str
    stage: str
    state: dict


class StateLogger:
    """Append state transitions to a JSON Lines log file."""

    def __init__(self, file_path: str | Path) -> None:
        self.path = Path(file_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")

    def log(self, state: PipelineState, stage: PipelineStage | str) -> None:
        """Record ``state`` at ``stage`` to the log file."""

        transition = StateTransition(
            timestamp=datetime.utcnow().isoformat(),
            pipeline_id=state.pipeline_id,
            stage=str(stage),
            state=state.to_dict(),
        )
        self._handle.write(json.dumps(asdict(transition)) + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()


class LogReplayer:
    """Iterate over transitions saved by :class:`StateLogger`."""

    def __init__(self, file_path: str | Path) -> None:
        self.path = Path(file_path)

    def transitions(self) -> Generator[StateTransition, None, None]:
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                data = json.loads(line)
                yield StateTransition(**data)

    def replay(self, delay: float = 0.5) -> None:
        """Print transitions sequentially with ``delay`` seconds between."""

        for t in self.transitions():
            print(f"[{t.timestamp}] {t.stage} -> {t.pipeline_id}")
            print(json.dumps(t.state, indent=2))
            time.sleep(delay)
