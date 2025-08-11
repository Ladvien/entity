"""Structured Output Validator Plugin for Entity Framework GPT-OSS Integration.

This plugin enforces structured output schemas using gpt-oss's native structured
output capabilities in the harmony format. It runs in the REVIEW stage to validate
outputs and ensure schema compliance.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type, Union

from pydantic import BaseModel, ValidationError, create_model

from entity.plugins.context import PluginContext
from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of schema validation with details."""

    is_valid: bool
    validated_data: Optional[Dict[str, Any]] = None
    errors: Optional[list] = None
    raw_output: Optional[str] = None
    regeneration_needed: bool = False


class StructuredOutputPlugin(Plugin):
    """Plugin that validates and enforces structured output schemas.

    This plugin runs in the REVIEW stage to validate that LLM outputs conform
    to specified JSON schemas. It can enforce strict compliance and request
    regeneration when outputs don't match the required structure.
    """

    supported_stages = [WorkflowExecutor.REVIEW]

    class ConfigModel(BaseModel):
        """Configuration for structured output validation."""

        output_schema: Optional[Type[BaseModel]] = None
        schema_dict: Optional[Dict[str, Any]] = None
        strict_mode: bool = True
        max_regeneration_attempts: int = 3
        allow_partial_match: bool = False
        extract_json_from_text: bool = True
        custom_error_messages: Optional[Dict[str, str]] = None
        validation_timeout: float = 5.0

        class Config:
            arbitrary_types_allowed = True

    def __init__(self, resources, config=None):
        """Initialize the structured output plugin.

        Args:
            resources: Entity framework resources
            config: Plugin configuration including schema definitions
        """
        super().__init__(resources, config)
        self._regeneration_count = 0
        self._schema_cache = {}

        # Validate configuration
        if not self.config.output_schema and not self.config.schema_dict:
            raise ValueError("Either output_schema or schema_dict must be provided")

    async def _execute_impl(self, context: PluginContext) -> str:
        """Execute structured output validation.

        Args:
            context: Plugin execution context containing the message to validate

        Returns:
            Validated and potentially corrected output string

        Raises:
            ValidationError: If validation fails and strict mode is enabled
        """
        logger.info("Starting structured output validation")

        try:
            # Extract and validate the output
            validation_result = await self._validate_output(context.message)

            if validation_result.is_valid:
                logger.info("Output validation successful")
                return validation_result.validated_data or context.message

            # Handle validation failure
            if self.config.strict_mode and validation_result.regeneration_needed:
                return await self._handle_regeneration(context, validation_result)

            # Non-strict mode: return original with warning
            logger.warning(
                f"Validation failed but continuing in non-strict mode: {validation_result.errors}"
            )
            return context.message

        except Exception as e:
            logger.error(f"Structured output validation error: {e}")
            if self.config.strict_mode:
                raise
            return context.message

    async def _validate_output(self, output: str) -> ValidationResult:
        """Validate output against the configured schema.

        Args:
            output: Raw output string to validate

        Returns:
            ValidationResult with validation details
        """
        try:
            # Extract JSON from output if needed
            if self.config.extract_json_from_text:
                json_data = self._extract_json_from_text(output)
            else:
                json_data = json.loads(output)

            # Get or create the validation schema
            schema = await self._get_validation_schema()

            # Validate against schema
            if isinstance(schema, type) and issubclass(schema, BaseModel):
                # Pydantic model validation
                validated = schema.model_validate(json_data)
                return ValidationResult(
                    is_valid=True,
                    validated_data=validated.model_dump_json(),
                    raw_output=output,
                )
            else:
                # JSON schema validation
                return await self._validate_with_json_schema(json_data, schema, output)

        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid JSON format: {e}"],
                raw_output=output,
                regeneration_needed=True,
            )
        except ValidationError as e:
            return ValidationResult(
                is_valid=False,
                errors=[str(error) for error in e.errors()],
                raw_output=output,
                regeneration_needed=True,
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {e}"],
                raw_output=output,
                regeneration_needed=True,
            )

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text that may contain other content.

        Args:
            text: Text potentially containing JSON

        Returns:
            Parsed JSON data

        Raises:
            json.JSONDecodeError: If no valid JSON found
        """
        # Try parsing the entire text first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Look for JSON blocks in markdown-style code blocks
        import re

        # Match JSON in code blocks
        json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        matches = re.findall(json_pattern, text, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Look for any JSON-like structure
        brace_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.findall(brace_pattern, text)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # If no JSON found, try to parse the whole thing
        raise json.JSONDecodeError("No valid JSON found in text", text, 0)

    async def _get_validation_schema(self) -> Union[Type[BaseModel], Dict[str, Any]]:
        """Get the validation schema from configuration.

        Returns:
            Either a Pydantic model class or JSON schema dict
        """
        if self.config.output_schema:
            return self.config.output_schema

        if self.config.schema_dict:
            # Create a dynamic Pydantic model from schema dict
            schema_key = json.dumps(self.config.schema_dict, sort_keys=True)

            if schema_key not in self._schema_cache:
                # Convert JSON schema to Pydantic model
                model_fields = {}
                properties = self.config.schema_dict.get("properties", {})
                required = self.config.schema_dict.get("required", [])

                for field_name, field_schema in properties.items():
                    field_type = self._json_type_to_python_type(field_schema)
                    default_value = ... if field_name in required else None
                    model_fields[field_name] = (field_type, default_value)

                # Create dynamic model
                DynamicModel = create_model("DynamicOutputModel", **model_fields)
                self._schema_cache[schema_key] = DynamicModel

            return self._schema_cache[schema_key]

        raise ValueError("No validation schema configured")

    def _json_type_to_python_type(self, field_schema: Dict[str, Any]) -> Type:
        """Convert JSON schema type to Python type.

        Args:
            field_schema: JSON schema field definition

        Returns:
            Corresponding Python type
        """
        json_type = field_schema.get("type", "string")

        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        return type_mapping.get(json_type, str)

    async def _validate_with_json_schema(
        self, data: Dict[str, Any], schema: Dict[str, Any], raw_output: str
    ) -> ValidationResult:
        """Validate data against JSON schema.

        Args:
            data: Parsed JSON data to validate
            schema: JSON schema to validate against
            raw_output: Original raw output string

        Returns:
            ValidationResult with validation details
        """
        try:
            # Basic JSON schema validation
            import jsonschema

            jsonschema.validate(data, schema)

            return ValidationResult(
                is_valid=True, validated_data=json.dumps(data), raw_output=raw_output
            )

        except ImportError:
            logger.warning("jsonschema not available, using basic validation")
            return ValidationResult(
                is_valid=True, validated_data=json.dumps(data), raw_output=raw_output
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Schema validation failed: {e}"],
                raw_output=raw_output,
                regeneration_needed=True,
            )

    async def _handle_regeneration(
        self, context: PluginContext, validation_result: ValidationResult
    ) -> str:
        """Handle output regeneration when validation fails.

        Args:
            context: Plugin execution context
            validation_result: Failed validation result

        Returns:
            Corrected output or raises ValidationError

        Raises:
            ValueError: If max regeneration attempts exceeded
        """
        self._regeneration_count += 1

        if self._regeneration_count > self.config.max_regeneration_attempts:
            error_msg = (
                f"Max regeneration attempts "
                f"({self.config.max_regeneration_attempts}) exceeded"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(
            f"Attempting output regeneration (attempt {self._regeneration_count})"
        )

        # Create enhanced context with validation feedback
        enhanced_context = await self._create_regeneration_context(
            context, validation_result
        )

        # Request regeneration through the LLM
        regenerated_output = await self._request_regeneration(enhanced_context)

        # Validate the regenerated output
        new_validation = await self._validate_output(regenerated_output)

        if new_validation.is_valid:
            logger.info("Regeneration successful")
            return new_validation.validated_data or regenerated_output

        # Recursive regeneration if still invalid
        return await self._handle_regeneration(context, new_validation)

    async def _create_regeneration_context(
        self, context: PluginContext, validation_result: ValidationResult
    ) -> PluginContext:
        """Create enhanced context for regeneration with validation feedback.

        Args:
            context: Original plugin context
            validation_result: Failed validation result

        Returns:
            Enhanced context with regeneration instructions
        """
        # Get schema information
        schema = await self._get_validation_schema()

        if isinstance(schema, type) and issubclass(schema, BaseModel):
            schema_info = schema.model_json_schema()
        else:
            schema_info = schema

        # Create regeneration message
        regeneration_message = self._create_regeneration_message(
            validation_result, schema_info
        )

        # Enhanced context (this would integrate with Entity's context system)
        enhanced_context = PluginContext(context.resources, context.user_id)
        enhanced_context.message = regeneration_message

        return enhanced_context

    def _create_regeneration_message(
        self, validation_result: ValidationResult, schema_info: Dict[str, Any]
    ) -> str:
        """Create message for regeneration request.

        Args:
            validation_result: Failed validation result
            schema_info: Schema information for guidance

        Returns:
            Formatted regeneration request message
        """
        error_details = "\n".join(validation_result.errors or [])

        message = f"""
The previous output did not conform to the required schema. Please regenerate the response.

VALIDATION ERRORS:
{error_details}

REQUIRED SCHEMA:
{json.dumps(schema_info, indent=2)}

ORIGINAL OUTPUT:
{validation_result.raw_output}

Please provide a response that strictly conforms to the schema above.
"""

        return message.strip()

    async def _request_regeneration(self, context: PluginContext) -> str:
        """Request output regeneration from the LLM.

        Args:
            context: Enhanced context with regeneration request

        Returns:
            Regenerated output string
        """
        # This would integrate with Entity's LLM infrastructure
        # For now, we'll use a placeholder that would be replaced with
        # actual LLM call through Entity's resources

        llm_resource = self.resources.get("llm")
        if llm_resource:
            response = await llm_resource.generate(
                context.message,
                user_id=context.user_id,
                timeout=self.config.validation_timeout,
            )
            return response

        # Fallback: return original message (would not happen in real implementation)
        logger.warning("No LLM resource available for regeneration")
        return context.message

    async def _should_execute(self, context: PluginContext) -> bool:
        """Determine if this plugin should execute for the given context.

        Args:
            context: Plugin execution context

        Returns:
            True if plugin should execute, False otherwise
        """
        # Only execute if we have a configured schema
        return (
            self.config.output_schema is not None or self.config.schema_dict is not None
        )

    def get_schema_info(self) -> Dict[str, Any]:
        """Get information about the configured schema.

        Returns:
            Schema information dictionary
        """
        if self.config.output_schema:
            return {
                "type": "pydantic_model",
                "model_name": self.config.output_schema.__name__,
                "schema": self.config.output_schema.model_json_schema(),
            }
        elif self.config.schema_dict:
            return {"type": "json_schema", "schema": self.config.schema_dict}
        else:
            return {"type": "none", "schema": None}
