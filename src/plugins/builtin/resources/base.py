from common_interfaces.resources import BaseResource as _BaseResource
from common_interfaces.resources import Resource
from pipeline.validation import ValidationResult


class BaseResource(_BaseResource):
    """Base resource with dependency validation stub."""

    @classmethod
    def validate_dependencies(cls, registry) -> ValidationResult:
        return ValidationResult.success_result()


__all__ = ["Resource", "BaseResource"]
