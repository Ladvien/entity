from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Union

from dotenv import load_dotenv


class VariableResolver:
    """Recursively substitutes ${VAR} patterns with environment values."""

    def __init__(self, env_file: str | None = None) -> None:
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()  # Auto-discovery

    def substitute(self, obj: Any) -> Any:
        return self.substitute_variables(obj)

    @classmethod
    def substitute_variables(cls, obj: Any) -> Any:
        """Recursively substitute ${VAR} patterns with environment values."""
        if isinstance(obj, str):
            return cls._replace_vars(obj)
        elif isinstance(obj, dict):
            return {k: cls.substitute_variables(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [cls.substitute_variables(elem) for elem in obj]
        return obj

    @staticmethod
    def _replace_vars(text: str) -> str:
        def replace_var(match):
            var_name = match.group(1)
            value = os.getenv(var_name)
            if value is None:
                raise ValueError(f"Environment variable ${{{var_name}}} not found")
            return value

        return re.sub(r'\$\{([^}]+)\}', replace_var, text)
