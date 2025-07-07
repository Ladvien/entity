from __future__ import annotations

"""Utilities for validating tool input parameters."""

import re
from html import escape
from typing import Any, Callable, Dict, Type

from pydantic import BaseModel, ValidationError

from pipeline.logging import get_logger

SQL_PATTERN = re.compile(r"(;|--|/\*|\b(drop|delete|insert|update)\b)", re.IGNORECASE)


def sanitize_text(text: str) -> str:
    """Return ``text`` escaped for HTML and checked for SQL injection."""
    if SQL_PATTERN.search(text):
        raise ValueError("Potential SQL injection detected")
    return escape(text)


class PluginInputValidator:
    """Validate and sanitize parameters using a Pydantic model."""

    def __init__(self, model: Type[BaseModel]) -> None:
        self.model = model
        self.logger = get_logger(self.__class__.__name__)

    def validate(self, params: Dict[str, Any]) -> BaseModel:
        """Parse ``params`` into ``model`` and sanitize string fields."""
        try:
            instance = self.model(**params)
        except ValidationError as exc:  # pragma: no cover - runtime error path
            self.logger.error(
                "parameter validation failed",
                exc_info=exc,
                extra={"pipeline_id": "n/a", "stage": "validation"},
            )
            raise

        if hasattr(instance, "model_dump"):
            data = instance.model_dump()
        else:  # pragma: no cover - pydantic v1 fallback
            data = instance.dict()
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = sanitize_text(value)
        return self.model(**data)

    def __call__(self, params: Dict[str, Any]) -> BaseModel:
        return self.validate(params)


def validate_params(
    model: Type[BaseModel],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator validating tool parameters with ``model``."""

    validator = PluginInputValidator(model)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Validate ``params`` before calling ``func``."""

        async def wrapper(
            self: Any, params: BaseModel | Dict[str, Any], *args: Any, **kwargs: Any
        ) -> Any:
            if isinstance(params, model):
                return await func(self, params, *args, **kwargs)
            try:
                validated = validator(params)
            except ValidationError as exc:
                raise ValueError(str(exc)) from exc
            return await func(self, validated, *args, **kwargs)

        return wrapper

    return decorator
