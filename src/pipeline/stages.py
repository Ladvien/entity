"""Pipeline component: stages."""

from enum import Enum, auto


class PipelineStage(Enum):
    PARSE = auto()
    THINK = auto()
    DO = auto()
    REVIEW = auto()
    DELIVER = auto()
    ERROR = auto()

    def __str__(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, name: str) -> "PipelineStage":
        try:
            return cls[name.upper()]
        except KeyError as exc:
            valid = ", ".join(s.name.lower() for s in cls)
            raise ValueError(f"Invalid stage '{name}'. Valid stages: {valid}") from exc

    @classmethod
    def ensure(cls, value: "PipelineStage | str") -> "PipelineStage":
        """Return ``PipelineStage`` for ``value`` or raise ``ValueError``."""

        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls.from_str(value)
        valid = ", ".join(s.name.lower() for s in cls)
        raise ValueError(f"Invalid stage '{value}'. Valid stages: {valid}")
