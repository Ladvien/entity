"""Stage enumeration for plugin execution."""

from __future__ import annotations

from enum import IntEnum


class PipelineStage(IntEnum):
    """Ordered pipeline stages."""

    INPUT = 1
    PARSE = 2
    THINK = 3
    DO = 4
    REVIEW = 5
    OUTPUT = 6
    ERROR = 7

    def __str__(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, value: str) -> "PipelineStage":
        try:
            return cls[value.upper()]
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Unknown stage: {value}") from exc

    @classmethod
    def ensure(cls, value: "PipelineStage | str") -> "PipelineStage":
        if isinstance(value, cls):
            return value
        return cls.from_str(str(value))


__all__ = ["PipelineStage"]
