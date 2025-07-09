from __future__ import annotations

"""Pipeline stage enumeration."""

from enum import Enum, auto


class PipelineStage(Enum):
    PARSE = auto()
    THINK = auto()
    DO = auto()
    DELIVER = auto()
    ERROR = auto()

    @classmethod
    def ensure(cls, value: "PipelineStage | str") -> "PipelineStage":
        if isinstance(value, cls):
            return value
        try:
            return cls[value.upper()]
        except KeyError as exc:
            raise ValueError(f"Invalid stage: {value}") from exc
