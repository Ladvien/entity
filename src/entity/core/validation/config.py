from __future__ import annotations

from typing import Any, Dict, Type

from pydantic import BaseModel, ValidationError

from entity.core.plugins import ValidationResult


def validate_model(model: Type[BaseModel], data: Dict[str, Any]) -> ValidationResult:
    """Parse ``data`` with ``model`` returning a :class:`ValidationResult`."""
    try:
        model.parse_obj(data)
    except ValidationError as exc:  # pragma: no cover - error path
        return ValidationResult.error_result(str(exc))
    return ValidationResult.success_result()
