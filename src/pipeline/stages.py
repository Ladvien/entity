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
    def from_str(cls, name: str) -> 'PipelineStage':
        try:
            return cls[name.upper()]
        except KeyError:
            valid = ', '.join(s.name.lower() for s in cls)
            raise ValueError(f"Invalid stage '{name}'. Valid stages: {valid}")
