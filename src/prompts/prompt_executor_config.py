from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
import yaml

# ─────────────────────────────────────────────────────────────────────────────
# Example, Configuration, and Loader Models
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class PromptExample:
    input_text: str
    expected_output: str
    explanation: Optional[str] = None


@dataclass
class PromptConfiguration:
    name: str  # Unique identifier
    technique_name: str  # e.g., "zero_shot", "chain_of_thought", "self_consistency"
    template: str  # Prompt template with variables
    system_message: Optional[str] = None  # Optional system-level instructions
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[PromptExample] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PromptConfiguration:
        examples_data = data.get("examples", [])
        examples = [PromptExample(**ex) for ex in examples_data]
        return cls(
            name=data["name"],
            technique_name=data["technique"],
            template=data["template"],
            system_message=data.get("system_message"),
            parameters=data.get("parameters", {}),
            examples=examples,
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> List[PromptConfiguration]:
        parsed = yaml.safe_load(yaml_str)
        if isinstance(parsed, dict):
            parsed = parsed.get("custom_prompts", [parsed])
        return [cls.from_dict(item) for item in parsed]


# ─────────────────────────────────────────────────────────────────────────────
# Optional: A wrapper model for a list of prompt configurations
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class PromptRegistry:
    prompts: List[PromptConfiguration]

    @classmethod
    def from_yaml(cls, yaml_str: str) -> PromptRegistry:
        prompts = PromptConfiguration.from_yaml(yaml_str)
        return cls(prompts=prompts)

    def get_by_name(self, name: str) -> Optional[PromptConfiguration]:
        return next((p for p in self.prompts if p.name == name), None)
