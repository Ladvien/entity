from enum import Enum, auto

<<<<<<< HEAD
class PipelineStage(Enum):
    """Execution stages for the pipeline."""

=======

class PipelineStage(Enum):
>>>>>>> c7b8e0ca4563f1fb9c781410e21cd0e9d18314fa
    PARSE = auto()
    THINK = auto()
    DO = auto()
    REVIEW = auto()
    DELIVER = auto()
    ERROR = auto()

    def __str__(self) -> str:
        return self.name.lower()

    @classmethod
<<<<<<< HEAD
    def from_str(cls, stage_name: str) -> "PipelineStage":
        """Create stage enum from string with validation."""
        try:
            return cls[stage_name.upper()]
        except KeyError:
            valid = [stage.name.lower() for stage in cls]
            raise ValueError(f"Invalid stage '{stage_name}'. Valid stages: {valid}")
=======
    def from_str(cls, name: str) -> "PipelineStage":
        try:
            return cls[name.upper()]
        except KeyError as exc:
            valid = ", ".join(s.name.lower() for s in cls)
            raise ValueError(f"Invalid stage '{name}'. Valid stages: {valid}") from exc
>>>>>>> c7b8e0ca4563f1fb9c781410e21cd0e9d18314fa
