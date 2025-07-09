from __future__ import annotations

"""Simple input validation utilities for plugin security experiments."""

import re
from html import escape
from typing import Any, Dict, Type

from pydantic import BaseModel, ValidationError

SQL_PATTERN = re.compile(r"(;|--|/\*|\b(drop|delete|insert|update)\b)", re.IGNORECASE)


def sanitize_text(text: str) -> str:
    """Escape HTML and block basic SQL injection patterns."""
    if SQL_PATTERN.search(text):
        raise ValueError("Potential SQL injection detected")
    return escape(text)


class InputValidator:
    """Validate and sanitize dictionaries using a Pydantic model."""

    def __init__(self, model: Type[BaseModel]) -> None:
        self._model = model

    def validate(self, params: Dict[str, Any]) -> BaseModel:
        try:
            instance = self._model(**params)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc

        if hasattr(instance, "model_dump"):
            data = instance.model_dump()
        else:  # pragma: no cover - pydantic v1 compatibility
            data = instance.dict()  # type: ignore[attr-defined]
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = sanitize_text(value)
        return self._model(**data)

    def __call__(self, params: Dict[str, Any]) -> BaseModel:
        return self.validate(params)
