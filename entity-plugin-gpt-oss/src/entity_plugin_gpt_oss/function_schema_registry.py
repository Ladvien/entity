"""Function Schema Registry Plugin for GPT-OSS Tool Management.

This plugin provides a centralized registry for function schemas that integrates
with gpt-oss's native function calling capabilities. It supports OpenAPI schema
definitions, parameter validation, versioning, and dynamic function registration.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class SchemaFormat(Enum):
    """Supported schema formats."""

    OPENAPI_3_0 = "openapi_3.0"
    OPENAPI_3_1 = "openapi_3.1"
    JSON_SCHEMA = "json_schema"
    PYDANTIC = "pydantic"
    HARMONY = "harmony"


class ParameterType(Enum):
    """Parameter types for function schemas."""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"
    ANY = "any"


class ValidationMode(Enum):
    """Validation modes for function parameters."""

    STRICT = "strict"  # Fail on any validation error
    PERMISSIVE = "permissive"  # Allow extra fields, coerce types
    PARTIAL = "partial"  # Allow missing optional fields


class FunctionParameter(BaseModel):
    """Definition of a function parameter."""

    name: str = Field(description="Parameter name")
    type: Union[ParameterType, List[ParameterType]] = Field(
        description="Parameter type(s)"
    )
    description: Optional[str] = Field(
        default=None, description="Parameter description"
    )
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Optional[Any] = Field(
        default=None, description="Default value if not provided"
    )
    enum: Optional[List[Any]] = Field(
        default=None, description="Allowed values for the parameter"
    )
    pattern: Optional[str] = Field(
        default=None, description="Regex pattern for string validation"
    )
    minimum: Optional[float] = Field(
        default=None, description="Minimum value for numbers"
    )
    maximum: Optional[float] = Field(
        default=None, description="Maximum value for numbers"
    )
    min_length: Optional[int] = Field(
        default=None, description="Minimum length for strings/arrays"
    )
    max_length: Optional[int] = Field(
        default=None, description="Maximum length for strings/arrays"
    )
    items: Optional[Dict[str, Any]] = Field(
        default=None, description="Schema for array items"
    )
    properties: Optional[Dict[str, Any]] = Field(
        default=None, description="Schema for object properties"
    )
    examples: Optional[List[Any]] = Field(default=None, description="Example values")


class FunctionSchema(BaseModel):
    """Complete schema definition for a function."""

    name: str = Field(description="Function name")
    description: str = Field(description="Function description")
    version: str = Field(default="1.0.0", description="Schema version")
    parameters: List[FunctionParameter] = Field(
        default_factory=list, description="Function parameters"
    )
    returns: Optional[Dict[str, Any]] = Field(
        default=None, description="Return value schema"
    )
    examples: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Example function calls"
    )
    deprecated: bool = Field(
        default=False, description="Whether function is deprecated"
    )
    deprecated_message: Optional[str] = Field(
        default=None, description="Deprecation message"
    )
    tags: List[str] = Field(
        default_factory=list, description="Function tags for categorization"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    harmony_compatible: bool = Field(
        default=True, description="Whether function is harmony-compatible"
    )
    validation_mode: ValidationMode = Field(
        default=ValidationMode.STRICT, description="Validation mode for parameters"
    )


class FunctionRegistration(BaseModel):
    """Registration record for a function."""

    schema: FunctionSchema = Field(description="Function schema")
    handler: Optional[str] = Field(
        default=None, description="Handler function path or identifier"
    )
    registered_at: datetime = Field(
        default_factory=datetime.now, description="Registration timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )
    usage_count: int = Field(
        default=0, description="Number of times function has been called"
    )
    last_used: Optional[datetime] = Field(
        default=None, description="Last usage timestamp"
    )
    enabled: bool = Field(default=True, description="Whether function is enabled")
    namespace: str = Field(default="default", description="Function namespace")
    access_level: str = Field(
        default="public", description="Access level (public/private/restricted)"
    )


class SchemaVersion(BaseModel):
    """Version information for a schema."""

    version: str = Field(description="Version identifier")
    schema: FunctionSchema = Field(description="Schema for this version")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(
        default=None, description="User who created version"
    )
    change_notes: Optional[str] = Field(
        default=None, description="Version change notes"
    )
    is_current: bool = Field(
        default=False, description="Whether this is the current version"
    )


class FunctionDiscoveryResult(BaseModel):
    """Result from function discovery."""

    total_functions: int = Field(description="Total number of functions found")
    matched_functions: List[FunctionSchema] = Field(
        description="Functions matching criteria"
    )
    namespaces: List[str] = Field(description="Available namespaces")
    tags: List[str] = Field(description="Available tags")
    query_time_ms: float = Field(description="Query execution time")


class ValidationResult(BaseModel):
    """Result from parameter validation."""

    valid: bool = Field(description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    coerced_values: Dict[str, Any] = Field(
        default_factory=dict, description="Values that were coerced"
    )
    missing_required: List[str] = Field(
        default_factory=list, description="Missing required parameters"
    )
    extra_fields: List[str] = Field(
        default_factory=list, description="Extra fields not in schema"
    )


class FunctionSchemaRegistryPlugin(Plugin):
    """Plugin that provides a centralized registry for function schemas.

    This plugin manages function schemas for gpt-oss tool calling, supporting:
    - OpenAPI schema definitions
    - Parameter validation
    - Schema versioning
    - Dynamic function registration
    - Function discovery
    - Harmony-compatible tool descriptions
    """

    supported_stages = [WorkflowExecutor.PARSE, WorkflowExecutor.DO]

    class ConfigModel(BaseModel):
        """Configuration for the function schema registry plugin."""

        # Core settings
        enabled: bool = Field(default=True, description="Enable schema registry")
        default_namespace: str = Field(
            default="default", description="Default namespace for functions"
        )
        allow_dynamic_registration: bool = Field(
            default=True, description="Allow runtime function registration"
        )

        # Validation settings
        default_validation_mode: ValidationMode = Field(
            default=ValidationMode.STRICT,
            description="Default validation mode for functions",
        )
        validate_on_registration: bool = Field(
            default=True, description="Validate schemas on registration"
        )
        allow_unknown_parameters: bool = Field(
            default=False, description="Allow parameters not in schema"
        )
        coerce_types: bool = Field(
            default=False, description="Attempt to coerce parameter types"
        )

        # Versioning settings
        enable_versioning: bool = Field(
            default=True, description="Enable schema versioning"
        )
        max_versions_per_function: int = Field(
            default=10,
            description="Maximum versions to keep per function",
            ge=1,
            le=100,
        )
        auto_increment_version: bool = Field(
            default=True, description="Auto-increment version on update"
        )

        # Discovery settings
        enable_discovery_api: bool = Field(
            default=True, description="Enable function discovery API"
        )
        discovery_cache_ttl_seconds: int = Field(
            default=300, description="Cache TTL for discovery results", ge=0, le=3600
        )
        max_discovery_results: int = Field(
            default=100,
            description="Maximum results for discovery queries",
            ge=1,
            le=1000,
        )

        # OpenAPI settings
        openapi_strict_mode: bool = Field(
            default=False, description="Strict OpenAPI compliance"
        )
        default_openapi_version: str = Field(
            default="3.0.3", description="Default OpenAPI version"
        )

        # Performance settings
        enable_caching: bool = Field(default=True, description="Enable schema caching")
        cache_size: int = Field(
            default=1000, description="Maximum cache entries", ge=100, le=10000
        )

        # Logging settings
        log_registrations: bool = Field(
            default=True, description="Log function registrations"
        )
        log_validations: bool = Field(
            default=False, description="Log validation operations"
        )
        log_discovery: bool = Field(default=False, description="Log discovery queries")

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize the function schema registry plugin."""
        super().__init__(resources, config)

        # Validate configuration
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")

        # Initialize registries
        self._function_registry: Dict[str, FunctionRegistration] = {}
        self._version_registry: Dict[str, List[SchemaVersion]] = {}
        self._namespace_index: Dict[str, Set[str]] = {"default": set()}
        self._tag_index: Dict[str, Set[str]] = {}

        # Initialize caches
        self._validation_cache: Dict[str, ValidationResult] = {}
        self._discovery_cache: Dict[str, Tuple[FunctionDiscoveryResult, float]] = {}
        self._openapi_cache: Dict[str, Dict[str, Any]] = {}

        # Initialize handlers
        self._function_handlers: Dict[str, Callable] = {}

        # Statistics
        self._stats = {
            "total_registrations": 0,
            "total_validations": 0,
            "total_discoveries": 0,
            "validation_failures": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    async def _execute_impl(self, context) -> str:
        """Execute schema registry operations."""
        try:
            # In PARSE stage, validate and prepare function schemas
            if context.current_stage == WorkflowExecutor.PARSE:
                return await self._process_parse_stage(context)

            # In DO stage, handle function execution with validation
            elif context.current_stage == WorkflowExecutor.DO:
                return await self._process_do_stage(context)

            return context.message

        except Exception as e:
            await context.log(
                level="error",
                category="function_schema_registry",
                message=f"Schema registry error: {str(e)}",
                error=str(e),
            )
            return context.message

    async def _process_parse_stage(self, context) -> str:
        """Process PARSE stage - prepare and validate function schemas."""
        # Look for function definitions in the message
        function_defs = await self._extract_function_definitions(context.message)

        if function_defs:
            # Register extracted functions
            for func_def in function_defs:
                await self.register_function(func_def, context)

            # Add registry info to context
            context.metadata["registered_functions"] = [f.name for f in function_defs]

        return context.message

    async def _process_do_stage(self, context) -> str:
        """Process DO stage - validate function calls."""
        # Look for function calls in the message
        function_calls = await self._extract_function_calls(context.message)

        if function_calls:
            # Validate each function call
            for call in function_calls:
                validation_result = await self.validate_function_call(
                    call["name"], call["parameters"]
                )

                if not validation_result.valid:
                    # Log validation failure
                    await context.log(
                        level="warning",
                        category="function_validation",
                        message=f"Function validation failed: {call['name']}",
                        errors=validation_result.errors,
                    )

                    # Optionally modify the message to indicate validation failure
                    if self.config.default_validation_mode == ValidationMode.STRICT:
                        return f"Function validation failed for {call['name']}: {', '.join(validation_result.errors)}"

        return context.message

    async def register_function(
        self,
        schema: Union[FunctionSchema, Dict[str, Any]],
        context: Optional[Any] = None,
        handler: Optional[Callable] = None,
        namespace: Optional[str] = None,
    ) -> bool:
        """Register a function schema.

        Args:
            schema: Function schema or dict to register
            context: Plugin context for logging
            handler: Optional handler function
            namespace: Optional namespace (defaults to config default)

        Returns:
            True if registration successful
        """
        try:
            # Convert dict to FunctionSchema if needed
            if isinstance(schema, dict):
                schema = FunctionSchema(**schema)

            # Validate schema if configured
            if self.config.validate_on_registration:
                validation_errors = self._validate_schema(schema)
                if validation_errors:
                    raise ValueError(
                        f"Schema validation failed: {', '.join(validation_errors)}"
                    )

            # Determine namespace
            namespace = namespace or self.config.default_namespace

            # Create registration key
            reg_key = f"{namespace}:{schema.name}"

            # Check for existing registration
            if reg_key in self._function_registry:
                if self.config.enable_versioning:
                    # Add as new version
                    await self._add_schema_version(reg_key, schema)
                else:
                    # Update existing
                    self._function_registry[reg_key].schema = schema
                    self._function_registry[reg_key].updated_at = datetime.now()
            else:
                # Create new registration
                registration = FunctionRegistration(
                    schema=schema,
                    handler=handler.__name__ if handler else None,
                    namespace=namespace,
                )
                self._function_registry[reg_key] = registration

                # Update indices
                if namespace not in self._namespace_index:
                    self._namespace_index[namespace] = set()
                self._namespace_index[namespace].add(schema.name)

                for tag in schema.tags:
                    if tag not in self._tag_index:
                        self._tag_index[tag] = set()
                    self._tag_index[tag].add(reg_key)

            # Store handler if provided
            if handler:
                self._function_handlers[reg_key] = handler

            # Update statistics
            self._stats["total_registrations"] += 1

            # Log registration if configured
            if self.config.log_registrations and context:
                await context.log(
                    level="info",
                    category="function_registry",
                    message=f"Registered function: {schema.name}",
                    namespace=namespace,
                    version=schema.version,
                )

            # Clear caches
            self._clear_caches()

            return True

        except Exception as e:
            if context:
                await context.log(
                    level="error",
                    category="function_registry",
                    message=f"Failed to register function: {str(e)}",
                    error=str(e),
                )
            return False

    async def validate_function_call(
        self,
        function_name: str,
        parameters: Dict[str, Any],
        namespace: Optional[str] = None,
    ) -> ValidationResult:
        """Validate function parameters against schema.

        Args:
            function_name: Name of function to validate
            parameters: Parameters to validate
            namespace: Optional namespace

        Returns:
            Validation result
        """
        # Make a copy of parameters to avoid modifying the original
        parameters = parameters.copy()

        # Generate cache key using original parameters
        cache_key = self._generate_validation_cache_key(
            function_name, parameters, namespace
        )

        # Check cache
        if self.config.enable_caching and cache_key in self._validation_cache:
            self._stats["cache_hits"] += 1
            return self._validation_cache[cache_key]

        self._stats["cache_misses"] += 1
        self._stats["total_validations"] += 1

        # Get function registration
        namespace = namespace or self.config.default_namespace
        reg_key = f"{namespace}:{function_name}"

        if reg_key not in self._function_registry:
            return ValidationResult(
                valid=False,
                errors=[
                    f"Function '{function_name}' not found in namespace '{namespace}'"
                ],
            )

        registration = self._function_registry[reg_key]
        schema = registration.schema

        # Check if function is enabled
        if not registration.enabled:
            return ValidationResult(
                valid=False, errors=[f"Function '{function_name}' is disabled"]
            )

        # Check if deprecated
        if schema.deprecated:
            warnings = [
                f"Function '{function_name}' is deprecated: {schema.deprecated_message or 'No message'}"
            ]
        else:
            warnings = []

        # Validate parameters
        result = self._validate_parameters(schema, parameters)
        result.warnings.extend(warnings)

        # Update usage statistics
        registration.usage_count += 1
        registration.last_used = datetime.now()

        # Cache result
        if self.config.enable_caching:
            self._validation_cache[cache_key] = result
            self._cleanup_cache_if_needed()

        # Track validation failures
        if not result.valid:
            self._stats["validation_failures"] += 1

        return result

    def _validate_parameters(
        self, schema: FunctionSchema, parameters: Dict[str, Any]
    ) -> ValidationResult:
        """Validate parameters against schema."""
        errors = []
        warnings = []
        coerced_values = {}
        missing_required = []
        extra_fields = []

        # Get validation mode
        validation_mode = schema.validation_mode

        # Check for required parameters and apply defaults
        for param in schema.parameters:
            if param.name not in parameters:
                if param.default is not None:
                    # Use default value
                    parameters[param.name] = param.default
                    coerced_values[param.name] = param.default
                elif param.required:
                    missing_required.append(param.name)

        # Validate provided parameters
        for param_name, param_value in parameters.items():
            # Find parameter schema
            param_schema = next(
                (p for p in schema.parameters if p.name == param_name), None
            )

            if not param_schema:
                if validation_mode == ValidationMode.STRICT:
                    extra_fields.append(param_name)
                elif not self.config.allow_unknown_parameters:
                    warnings.append(f"Unknown parameter: {param_name}")
                continue

            # Check if this was a default value that was applied
            if param_name in coerced_values:
                # Skip validation for already coerced default values
                continue

            # Validate parameter value
            param_errors = self._validate_parameter_value(
                param_schema, param_value, coerced_values
            )
            errors.extend(param_errors)

        # Compile errors
        if missing_required:
            errors.append(f"Missing required parameters: {', '.join(missing_required)}")

        if extra_fields and validation_mode == ValidationMode.STRICT:
            errors.append(f"Extra parameters not allowed: {', '.join(extra_fields)}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            coerced_values=coerced_values,
            missing_required=missing_required,
            extra_fields=extra_fields,
        )

    def _validate_parameter_value(
        self, param: FunctionParameter, value: Any, coerced_values: Dict[str, Any]
    ) -> List[str]:
        """Validate a single parameter value."""
        errors = []

        # Type validation
        expected_types = param.type if isinstance(param.type, list) else [param.type]
        value_type = self._get_value_type(value)

        if value_type not in expected_types and ParameterType.ANY not in expected_types:
            if self.config.coerce_types:
                # Try to coerce
                coerced = self._try_coerce_type(value, expected_types[0])
                if coerced is not None:
                    coerced_values[param.name] = coerced
                    value = coerced
                else:
                    errors.append(
                        f"Parameter '{param.name}' expects {expected_types} but got {value_type}"
                    )
            else:
                errors.append(
                    f"Parameter '{param.name}' expects {expected_types} but got {value_type}"
                )

        # Enum validation
        if param.enum and value not in param.enum:
            errors.append(f"Parameter '{param.name}' must be one of {param.enum}")

        # Pattern validation for strings
        if param.pattern and isinstance(value, str):
            if not re.match(param.pattern, value):
                errors.append(
                    f"Parameter '{param.name}' does not match pattern '{param.pattern}'"
                )

        # Range validation for numbers
        if isinstance(value, (int, float)):
            if param.minimum is not None and value < param.minimum:
                errors.append(f"Parameter '{param.name}' must be >= {param.minimum}")
            if param.maximum is not None and value > param.maximum:
                errors.append(f"Parameter '{param.name}' must be <= {param.maximum}")

        # Length validation
        if isinstance(value, (str, list, dict)):
            length = len(value)
            if param.min_length is not None and length < param.min_length:
                errors.append(
                    f"Parameter '{param.name}' must have length >= {param.min_length}"
                )
            if param.max_length is not None and length > param.max_length:
                errors.append(
                    f"Parameter '{param.name}' must have length <= {param.max_length}"
                )

        return errors

    def _get_value_type(self, value: Any) -> ParameterType:
        """Get parameter type for a value."""
        if value is None:
            return ParameterType.NULL
        elif isinstance(value, bool):
            return ParameterType.BOOLEAN
        elif isinstance(value, int):
            return ParameterType.INTEGER
        elif isinstance(value, float):
            return ParameterType.NUMBER
        elif isinstance(value, str):
            return ParameterType.STRING
        elif isinstance(value, list):
            return ParameterType.ARRAY
        elif isinstance(value, dict):
            return ParameterType.OBJECT
        else:
            return ParameterType.ANY

    def _try_coerce_type(self, value: Any, target_type: ParameterType) -> Optional[Any]:
        """Try to coerce value to target type."""
        try:
            if target_type == ParameterType.STRING:
                return str(value)
            elif target_type == ParameterType.INTEGER:
                return int(value)
            elif target_type == ParameterType.NUMBER:
                return float(value)
            elif target_type == ParameterType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ["true", "1", "yes", "on"]
                return bool(value)
            elif target_type == ParameterType.ARRAY:
                if not isinstance(value, list):
                    return [value]
                return value
            elif target_type == ParameterType.OBJECT:
                if isinstance(value, str):
                    return json.loads(value)
                return dict(value)
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
        return None

    async def discover_functions(
        self,
        namespace: Optional[str] = None,
        tags: Optional[List[str]] = None,
        name_pattern: Optional[str] = None,
        include_deprecated: bool = False,
    ) -> FunctionDiscoveryResult:
        """Discover functions based on criteria.

        Args:
            namespace: Filter by namespace
            tags: Filter by tags
            name_pattern: Regex pattern for function names
            include_deprecated: Include deprecated functions

        Returns:
            Discovery result
        """
        start_time = datetime.now()
        self._stats["total_discoveries"] += 1

        # Generate cache key
        cache_key = self._generate_discovery_cache_key(
            namespace, tags, name_pattern, include_deprecated
        )

        # Check cache
        if self.config.enable_caching and cache_key in self._discovery_cache:
            cached_result, cached_time = self._discovery_cache[cache_key]
            if (
                datetime.now().timestamp() - cached_time
            ) < self.config.discovery_cache_ttl_seconds:
                self._stats["cache_hits"] += 1
                return cached_result

        self._stats["cache_misses"] += 1

        # Filter functions
        matched_functions = []

        for reg_key, registration in self._function_registry.items():
            schema = registration.schema

            # Check namespace
            if namespace and registration.namespace != namespace:
                continue

            # Check tags
            if tags and not any(tag in schema.tags for tag in tags):
                continue

            # Check name pattern
            if name_pattern and not re.match(name_pattern, schema.name):
                continue

            # Check deprecated
            if not include_deprecated and schema.deprecated:
                continue

            # Check enabled
            if not registration.enabled:
                continue

            matched_functions.append(schema)

            # Limit results
            if len(matched_functions) >= self.config.max_discovery_results:
                break

        # Build result
        result = FunctionDiscoveryResult(
            total_functions=len(self._function_registry),
            matched_functions=matched_functions,
            namespaces=list(self._namespace_index.keys()),
            tags=list(self._tag_index.keys()),
            query_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
        )

        # Cache result
        if self.config.enable_caching:
            self._discovery_cache[cache_key] = (result, datetime.now().timestamp())

        return result

    def get_harmony_description(
        self, function_name: str, namespace: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get harmony-compatible tool description for a function.

        Args:
            function_name: Function name
            namespace: Optional namespace

        Returns:
            Harmony format description or None if not found
        """
        namespace = namespace or self.config.default_namespace
        reg_key = f"{namespace}:{function_name}"

        if reg_key not in self._function_registry:
            return None

        registration = self._function_registry[reg_key]
        schema = registration.schema

        if not schema.harmony_compatible:
            return None

        # Build harmony format
        harmony_desc = {
            "type": "function",
            "function": {
                "name": schema.name,
                "description": schema.description,
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }

        # Add parameters
        for param in schema.parameters:
            param_schema = {
                "type": (
                    param.type.value
                    if isinstance(param.type, ParameterType)
                    else "string"
                ),
                "description": param.description or "",
            }

            if param.enum:
                param_schema["enum"] = param.enum
            if param.pattern:
                param_schema["pattern"] = param.pattern
            if param.minimum is not None:
                param_schema["minimum"] = param.minimum
            if param.maximum is not None:
                param_schema["maximum"] = param.maximum

            harmony_desc["function"]["parameters"]["properties"][param.name] = (
                param_schema
            )

            if param.required:
                harmony_desc["function"]["parameters"]["required"].append(param.name)

        return harmony_desc

    def export_openapi_schema(
        self, namespace: Optional[str] = None, version: str = "3.0.3"
    ) -> Dict[str, Any]:
        """Export functions as OpenAPI schema.

        Args:
            namespace: Optional namespace filter
            version: OpenAPI version

        Returns:
            OpenAPI schema document
        """
        # Check cache
        cache_key = f"openapi:{namespace}:{version}"
        if cache_key in self._openapi_cache:
            return self._openapi_cache[cache_key]

        # Build OpenAPI document
        openapi_doc = {
            "openapi": version,
            "info": {
                "title": f"Function Schema Registry - {namespace or 'All'}",
                "version": "1.0.0",
                "description": "Auto-generated OpenAPI schema from function registry",
            },
            "paths": {},
            "components": {"schemas": {}},
        }

        # Add functions as paths
        for reg_key, registration in self._function_registry.items():
            if namespace and registration.namespace != namespace:
                continue

            schema = registration.schema

            # Create path
            path = f"/{registration.namespace}/{schema.name}"

            # Build operation
            operation = {
                "summary": schema.description,
                "operationId": schema.name,
                "tags": schema.tags,
                "deprecated": schema.deprecated,
            }

            # Add parameters
            if schema.parameters:
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": self._build_openapi_schema(schema)
                        }
                    }
                }

            # Add response
            operation["responses"] = {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": schema.returns or {"type": "object"}
                        }
                    },
                }
            }

            openapi_doc["paths"][path] = {"post": operation}

        # Cache result
        self._openapi_cache[cache_key] = openapi_doc

        return openapi_doc

    def _build_openapi_schema(self, function_schema: FunctionSchema) -> Dict[str, Any]:
        """Build OpenAPI schema for function parameters."""
        schema = {"type": "object", "properties": {}, "required": []}

        for param in function_schema.parameters:
            param_schema = {
                "type": (
                    param.type.value
                    if isinstance(param.type, ParameterType)
                    else "string"
                )
            }

            if param.description:
                param_schema["description"] = param.description
            if param.enum:
                param_schema["enum"] = param.enum
            if param.pattern:
                param_schema["pattern"] = param.pattern
            if param.minimum is not None:
                param_schema["minimum"] = param.minimum
            if param.maximum is not None:
                param_schema["maximum"] = param.maximum
            if param.min_length is not None:
                param_schema["minLength"] = param.min_length
            if param.max_length is not None:
                param_schema["maxLength"] = param.max_length
            if param.default is not None:
                param_schema["default"] = param.default
            if param.examples:
                param_schema["examples"] = param.examples

            schema["properties"][param.name] = param_schema

            if param.required:
                schema["required"].append(param.name)

        return schema

    async def add_schema_version(
        self,
        function_name: str,
        schema: FunctionSchema,
        namespace: Optional[str] = None,
        change_notes: Optional[str] = None,
    ) -> bool:
        """Add a new version of a function schema.

        Args:
            function_name: Function name
            schema: New schema version
            namespace: Optional namespace
            change_notes: Optional change notes

        Returns:
            True if version added successfully
        """
        namespace = namespace or self.config.default_namespace
        reg_key = f"{namespace}:{function_name}"

        if reg_key not in self._function_registry:
            return False

        # Auto-increment version if configured and version matches current
        if self.config.auto_increment_version:
            current_version = self._function_registry[reg_key].schema.version
            if schema.version == current_version:
                schema.version = self._increment_version(schema.version)

        # Create version entry
        version_entry = SchemaVersion(
            version=schema.version,
            schema=schema,
            change_notes=change_notes,
            is_current=True,
        )

        # Update version registry
        if reg_key not in self._version_registry:
            self._version_registry[reg_key] = []

        # Mark previous versions as not current
        for v in self._version_registry[reg_key]:
            v.is_current = False

        # Add new version
        self._version_registry[reg_key].append(version_entry)

        # Limit versions if configured
        if len(self._version_registry[reg_key]) > self.config.max_versions_per_function:
            self._version_registry[reg_key] = self._version_registry[reg_key][
                -self.config.max_versions_per_function :
            ]

        # Update main registry
        self._function_registry[reg_key].schema = schema
        self._function_registry[reg_key].updated_at = datetime.now()

        # Clear caches
        self._clear_caches()

        return True

    def _increment_version(self, version: str) -> str:
        """Increment semantic version."""
        parts = version.split(".")
        if len(parts) == 3:
            # Increment patch version
            parts[2] = str(int(parts[2]) + 1)
        else:
            # Default to 1.0.1
            return "1.0.1"
        return ".".join(parts)

    def get_function_versions(
        self, function_name: str, namespace: Optional[str] = None
    ) -> List[SchemaVersion]:
        """Get all versions of a function schema.

        Args:
            function_name: Function name
            namespace: Optional namespace

        Returns:
            List of schema versions
        """
        namespace = namespace or self.config.default_namespace
        reg_key = f"{namespace}:{function_name}"

        return self._version_registry.get(reg_key, [])

    def _validate_schema(self, schema: FunctionSchema) -> List[str]:
        """Validate a function schema."""
        errors = []

        # Validate name
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", schema.name):
            errors.append(
                "Function name must start with letter and contain only alphanumeric and underscore"
            )

        # Validate version
        if not re.match(r"^\d+\.\d+\.\d+$", schema.version):
            errors.append("Version must follow semantic versioning (x.y.z)")

        # Validate parameters
        param_names = set()
        for param in schema.parameters:
            if param.name in param_names:
                errors.append(f"Duplicate parameter name: {param.name}")
            param_names.add(param.name)

            # Validate parameter
            param_errors = self._validate_parameter_schema(param)
            errors.extend(param_errors)

        return errors

    def _validate_parameter_schema(self, param: FunctionParameter) -> List[str]:
        """Validate a parameter schema."""
        errors = []

        # Validate name
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", param.name):
            errors.append(f"Parameter name '{param.name}' invalid")

        # Validate pattern if present
        if param.pattern:
            try:
                re.compile(param.pattern)
            except re.error:
                errors.append(f"Invalid regex pattern for parameter '{param.name}'")

        # Validate min/max
        if param.minimum is not None and param.maximum is not None:
            if param.minimum > param.maximum:
                errors.append(f"Minimum > maximum for parameter '{param.name}'")

        if param.min_length is not None and param.max_length is not None:
            if param.min_length > param.max_length:
                errors.append(f"Min length > max length for parameter '{param.name}'")

        return errors

    async def _extract_function_definitions(self, message: str) -> List[FunctionSchema]:
        """Extract function definitions from message."""
        functions = []

        # Look for function definition patterns
        # Pattern: @function(name="...", description="...")
        pattern = r"@function\((.*?)\)"
        matches = re.finditer(pattern, message, re.DOTALL)

        for match in matches:
            try:
                # Parse function definition
                func_str = match.group(1)
                # This is a simplified parser - in production, use proper parsing
                func_dict = eval(f"dict({func_str})")
                functions.append(FunctionSchema(**func_dict))
            except Exception:
                pass

        return functions

    async def _extract_function_calls(self, message: str) -> List[Dict[str, Any]]:
        """Extract function calls from message."""
        calls = []

        # Look for function call patterns
        # Pattern: function_name(param1=value1, param2=value2)
        pattern = r"([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)"
        matches = re.finditer(pattern, message, re.DOTALL)

        for match in matches:
            try:
                func_name = match.group(1)
                params_str = match.group(2)

                # Parse parameters (simplified)
                if params_str:
                    # This is a simplified parser - in production, use proper parsing
                    params = eval(f"dict({params_str})")
                else:
                    params = {}

                calls.append({"name": func_name, "parameters": params})
            except Exception:
                pass

        return calls

    def _generate_validation_cache_key(
        self, function_name: str, parameters: Dict[str, Any], namespace: Optional[str]
    ) -> str:
        """Generate cache key for validation."""
        key_parts = [
            namespace or self.config.default_namespace,
            function_name,
            json.dumps(parameters, sort_keys=True),
        ]
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _generate_discovery_cache_key(
        self,
        namespace: Optional[str],
        tags: Optional[List[str]],
        name_pattern: Optional[str],
        include_deprecated: bool,
    ) -> str:
        """Generate cache key for discovery."""
        key_parts = [
            namespace or "",
            ",".join(sorted(tags)) if tags else "",
            name_pattern or "",
            str(include_deprecated),
        ]
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _clear_caches(self):
        """Clear all caches."""
        self._validation_cache.clear()
        self._discovery_cache.clear()
        self._openapi_cache.clear()

    def _cleanup_cache_if_needed(self):
        """Clean up cache if it exceeds size limit."""
        if len(self._validation_cache) > self.config.cache_size:
            # Remove oldest entries (simple FIFO)
            items_to_remove = len(self._validation_cache) - self.config.cache_size
            for key in list(self._validation_cache.keys())[:items_to_remove]:
                del self._validation_cache[key]

    async def _add_schema_version(self, reg_key: str, schema: FunctionSchema):
        """Add a new schema version (internal helper)."""
        await self.add_schema_version(
            schema.name,
            schema,
            namespace=reg_key.split(":")[0],
            change_notes="Auto-versioned update",
        )

    # Public API methods

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_functions": len(self._function_registry),
            "total_namespaces": len(self._namespace_index),
            "total_tags": len(self._tag_index),
            "total_versions": sum(len(v) for v in self._version_registry.values()),
            "cache_size": len(self._validation_cache),
            "stats": self._stats,
        }

    def get_function(
        self, function_name: str, namespace: Optional[str] = None
    ) -> Optional[FunctionSchema]:
        """Get a function schema.

        Args:
            function_name: Function name
            namespace: Optional namespace

        Returns:
            Function schema or None if not found
        """
        namespace = namespace or self.config.default_namespace
        reg_key = f"{namespace}:{function_name}"

        registration = self._function_registry.get(reg_key)
        return registration.schema if registration else None

    def list_functions(self, namespace: Optional[str] = None) -> List[str]:
        """List all function names.

        Args:
            namespace: Optional namespace filter

        Returns:
            List of function names
        """
        if namespace:
            return list(self._namespace_index.get(namespace, set()))
        else:
            return [reg.schema.name for reg in self._function_registry.values()]

    def delete_function(
        self, function_name: str, namespace: Optional[str] = None
    ) -> bool:
        """Delete a function from registry.

        Args:
            function_name: Function name
            namespace: Optional namespace

        Returns:
            True if deleted successfully
        """
        namespace = namespace or self.config.default_namespace
        reg_key = f"{namespace}:{function_name}"

        if reg_key not in self._function_registry:
            return False

        # Remove from registry
        registration = self._function_registry[reg_key]
        del self._function_registry[reg_key]

        # Update indices
        if namespace in self._namespace_index:
            self._namespace_index[namespace].discard(function_name)

        for tag in registration.schema.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(reg_key)

        # Remove versions
        if reg_key in self._version_registry:
            del self._version_registry[reg_key]

        # Remove handler
        if reg_key in self._function_handlers:
            del self._function_handlers[reg_key]

        # Clear caches
        self._clear_caches()

        return True

    def enable_function(
        self, function_name: str, namespace: Optional[str] = None, enabled: bool = True
    ) -> bool:
        """Enable or disable a function.

        Args:
            function_name: Function name
            namespace: Optional namespace
            enabled: Whether to enable or disable

        Returns:
            True if updated successfully
        """
        namespace = namespace or self.config.default_namespace
        reg_key = f"{namespace}:{function_name}"

        if reg_key not in self._function_registry:
            return False

        self._function_registry[reg_key].enabled = enabled
        self._function_registry[reg_key].updated_at = datetime.now()

        return True
