from enum import Enum


class PluginStage(str, Enum):
    INPUT = "input"
    PROMPT_PRE = "prompt_preprocessing"
    PROMPT = "prompt_processing"
    TOOL = "tool_use"
    OUTPUT = "output"


class PluginType(str, Enum):
    RESOURCE = "resource"
    TOOL = "tool"
    PROMPT = "prompt"
