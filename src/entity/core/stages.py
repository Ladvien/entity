"""Stage enumeration for plugin execution."""

from __future__ import annotations

from enum import IntEnum, auto


class PipelineStage(IntEnum):
    """Ordered pipeline stages."""

    INPUT = auto()
    PARSE = auto()
    THINK = auto()
    DO = auto()
    REVIEW = auto()
    OUTPUT = auto()
    ERROR = auto()

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
