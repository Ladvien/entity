from __future__ import annotations

"""Enumeration of pipeline execution stages."""

from enum import Enum, auto


class PipelineStage(Enum):
    PARSE = auto()
    THINK = auto()
    DO = auto()
    REVIEW = auto()
    DELIVER = auto()
    ERROR = auto()

    @classmethod
    def ensure(cls, value: "PipelineStage | str") -> "PipelineStage":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            try:
                return cls[value.upper()]
            except KeyError as exc:  # pragma: no cover - defensive
                raise ValueError(f"Invalid stage: {value}") from exc
        raise ValueError(f"Invalid stage: {value}")

    def __str__(self) -> str:  # pragma: no cover - formatting helper
        return self.name.lower()
