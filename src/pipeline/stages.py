from enum import Enum, auto

class PipelineStage(Enum):
    """Execution stages for the pipeline."""

    PARSE = auto()
    THINK = auto()
    DO = auto()
    REVIEW = auto()
    DELIVER = auto()
    ERROR = auto()

    def __str__(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, stage_name: str) -> "PipelineStage":
        """Create stage enum from string with validation."""
        try:
            return cls[stage_name.upper()]
        except KeyError:
            valid = [stage.name.lower() for stage in cls]
            raise ValueError(f"Invalid stage '{stage_name}'. Valid stages: {valid}")
