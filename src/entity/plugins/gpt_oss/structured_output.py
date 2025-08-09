"""Structured Output Validator Plugin for GPT-OSS integration.

This plugin enforces structured output schemas using gpt-oss's native structured
output capabilities in the harmony format. It validates outputs in the REVIEW stage
and can request regeneration if validation fails.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Type

from pydantic import BaseModel, Field, ValidationError

from entity.plugins.base import Plugin
from entity.plugins.validation import ValidationResult
from entity.workflow.executor import WorkflowExecutor


class StructuredOutputValidationError(Exception):
    """Exception raised when structured output validation fails."""
    
    def __init__(self, message: str, validation_errors: list[str], original_output: str):
        self.message = message
        self.validation_errors = validation_errors
        self.original_output = original_output
        super().__init__(message)


class SchemaValidationResult(BaseModel):
    """Result of schema validation."""
    
    valid: bool
    validated_data: Dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)
    original_output: str = ""
    regeneration_prompt: str | None = None


class StructuredOutputPlugin(Plugin):
    """Plugin that enforces structured output schemas in the REVIEW stage.
    
    This plugin:
    - Validates LLM outputs against Pydantic schema models
    - Provides clear error messages for schema violations
    - Supports nested and complex schemas
    - Can request regeneration with stricter constraints
    - Integrates with Entity's validation framework
    """
    
    supported_stages = [WorkflowExecutor.REVIEW]
    dependencies = ["llm", "memory"]
    
    class ConfigModel(BaseModel):
        """Configuration for the structured output validator."""
        
        # Schema configuration
        output_schema: Type[BaseModel] | None = Field(
            default=None, description="Pydantic model for output validation"
        )
        schema_definition: Dict[str, Any] | None = Field(
            default=None, description="JSON schema definition"
        )
        
        # Validation behavior
        strict_mode: bool = Field(
            default=True, description="Strict validation - fail on any schema violation"
        )
        allow_extra_fields: bool = Field(
            default=False, description="Allow extra fields not in schema"
        )
        coerce_types: bool = Field(
            default=True, description="Attempt to coerce types when possible"
        )
        
        # Regeneration settings
        max_regeneration_attempts: int = Field(
            default=2, description="Maximum regeneration attempts", ge=0, le=10
        )
        enable_regeneration: bool = Field(
            default=True, description="Enable automatic regeneration on validation failure"
        )
        
        # Error handling
        provide_examples: bool = Field(
            default=True, description="Include schema examples in error messages"
        )
        detailed_errors: bool = Field(
            default=True, description="Provide detailed validation error messages"
        )
        
        # Integration settings
        preserve_original_on_failure: bool = Field(
            default=True, description="Keep original output if validation fails"
        )

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize the structured output validator plugin."""
        super().__init__(resources, config)
        
        # Validate configuration
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")
        
        # Initialize schema from config
        self.output_schema = None
        if self.config.output_schema:
            self.output_schema = self.config.output_schema
        elif self.config.schema_definition:
            # TODO: Convert JSON schema to dynamic Pydantic model
            pass
    
    async def _execute_impl(self, context) -> str:
        """Execute structured output validation in REVIEW stage."""
        if not self.output_schema and not self.config.schema_definition:
            # No schema configured, pass through
            return context.message
        
        # Track regeneration attempts
        attempt_count = await context.recall("structured_output_attempts", 0)
        
        try:
            # Validate the current message against schema
            validation_result = await self._validate_output(context.message)
            
            if validation_result.valid:
                # Reset attempt counter on success
                await context.remember("structured_output_attempts", 0)
                
                # Log successful validation
                await context.log(
                    level="info",
                    category="schema_validation",
                    message="Output successfully validated against schema",
                    schema_type=self.output_schema.__name__ if self.output_schema else "json_schema"
                )
                
                # Return validated and potentially reformatted output
                if validation_result.validated_data:
                    return json.dumps(validation_result.validated_data, indent=2)
                return context.message
            
            else:
                # Validation failed
                await context.log(
                    level="warning", 
                    category="schema_validation",
                    message=f"Schema validation failed: {'; '.join(validation_result.errors)}",
                    attempt_count=attempt_count,
                    max_attempts=self.config.max_regeneration_attempts
                )
                
                # Check if we should attempt regeneration
                if (self.config.enable_regeneration and 
                    attempt_count < self.config.max_regeneration_attempts):
                    
                    # Increment attempt counter
                    await context.remember("structured_output_attempts", attempt_count + 1)
                    
                    # Request regeneration with improved prompt
                    regeneration_prompt = self._create_regeneration_prompt(
                        validation_result.errors,
                        validation_result.original_output
                    )
                    
                    # Store regeneration context for potential LLM retry
                    await context.remember("regeneration_required", True)
                    await context.remember("regeneration_prompt", regeneration_prompt)
                    await context.remember("validation_errors", validation_result.errors)
                    
                    # In a real implementation, we'd trigger LLM regeneration here
                    # For now, we'll raise an exception to indicate validation failure
                    raise StructuredOutputValidationError(
                        f"Schema validation failed after attempt {attempt_count + 1}",
                        validation_result.errors,
                        validation_result.original_output
                    )
                
                else:
                    # Max attempts reached or regeneration disabled
                    if self.config.preserve_original_on_failure:
                        await context.log(
                            level="error",
                            category="schema_validation", 
                            message="Max regeneration attempts reached, preserving original output",
                            validation_errors=validation_result.errors
                        )
                        return context.message
                    else:
                        # Fail hard
                        raise StructuredOutputValidationError(
                            "Schema validation failed and regeneration limit exceeded",
                            validation_result.errors,
                            validation_result.original_output
                        )
        
        except StructuredOutputValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Log unexpected errors
            await context.log(
                level="error",
                category="schema_validation",
                message=f"Unexpected error during validation: {str(e)}"
            )
            
            if self.config.preserve_original_on_failure:
                return context.message
            else:
                raise
    
    async def _validate_output(self, output: str) -> SchemaValidationResult:
        """Validate output against configured schema."""
        if not self.output_schema:
            return SchemaValidationResult(
                valid=True,
                original_output=output
            )
        
        try:
            # Try to parse as JSON first
            try:
                parsed_data = json.loads(output)
            except json.JSONDecodeError as e:
                return SchemaValidationResult(
                    valid=False,
                    errors=[f"Output is not valid JSON: {str(e)}"],
                    original_output=output
                )
            
            # Validate against Pydantic model
            if isinstance(parsed_data, dict):
                try:
                    validated = self.output_schema(**parsed_data)
                    return SchemaValidationResult(
                        valid=True,
                        validated_data=validated.model_dump(),
                        original_output=output
                    )
                except ValidationError as e:
                    # Extract detailed error messages
                    error_messages = []
                    for error in e.errors():
                        field_path = " -> ".join(str(loc) for loc in error["loc"])
                        error_messages.append(f"{field_path}: {error['msg']}")
                    
                    return SchemaValidationResult(
                        valid=False,
                        errors=error_messages,
                        original_output=output
                    )
            
            else:
                # Try direct validation for non-dict types
                try:
                    validated = self.output_schema(parsed_data)
                    return SchemaValidationResult(
                        valid=True,
                        validated_data=validated.model_dump() if hasattr(validated, 'model_dump') else validated,
                        original_output=output
                    )
                except (ValidationError, TypeError) as e:
                    return SchemaValidationResult(
                        valid=False,
                        errors=[f"Schema validation failed: {str(e)}"],
                        original_output=output
                    )
                    
        except Exception as e:
            return SchemaValidationResult(
                valid=False,
                errors=[f"Validation error: {str(e)}"],
                original_output=output
            )
    
    def _create_regeneration_prompt(self, validation_errors: list[str], original_output: str) -> str:
        """Create a prompt for LLM regeneration based on validation errors."""
        error_summary = "\n".join(f"- {error}" for error in validation_errors)
        
        schema_info = ""
        if self.output_schema and self.config.provide_examples:
            schema_info = f"\n\nRequired schema:\n{json.dumps(self.output_schema.model_json_schema(), indent=2)}"
            
            # Try to provide an example
            try:
                # Create example instance with default values
                example = self.output_schema()
                schema_info += f"\n\nExample valid output:\n{json.dumps(example.model_dump(), indent=2)}"
            except Exception:
                # Can't create example, skip
                pass
        
        return f"""The previous output did not conform to the required schema. Please regenerate with these issues fixed:

{error_summary}

Original output that failed validation:
{original_output}
{schema_info}

Please provide a new response that strictly conforms to the required schema."""
    
    def set_schema(self, schema: Type[BaseModel]) -> None:
        """Dynamically set the output schema."""
        self.output_schema = schema
        # Update config to reflect the change
        self.config.output_schema = schema
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get information about the current schema."""
        if not self.output_schema:
            return {"schema_configured": False}
        
        return {
            "schema_configured": True,
            "schema_name": self.output_schema.__name__,
            "schema_json": self.output_schema.model_json_schema(),
            "config": {
                "strict_mode": self.config.strict_mode,
                "enable_regeneration": self.config.enable_regeneration,
                "max_attempts": self.config.max_regeneration_attempts
            }
        }
    
    async def validate_standalone(self, output: str) -> SchemaValidationResult:
        """Validate output without context (for testing/external use)."""
        return await self._validate_output(output)