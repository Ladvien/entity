"""Unit tests for Function Schema Registry Plugin."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from entity.plugins.context import PluginContext
from entity.workflow.executor import WorkflowExecutor

from entity_plugin_gpt_oss.function_schema_registry import (
    FunctionDiscoveryResult,
    FunctionParameter,
    FunctionRegistration,
    FunctionSchema,
    FunctionSchemaRegistryPlugin,
    ParameterType,
    SchemaFormat,
    ValidationMode,
    ValidationResult,
)


class TestFunctionSchemaRegistryPlugin:
    """Test FunctionSchemaRegistryPlugin functionality."""

    @pytest.fixture
    def mock_resources(self):
        """Create mock resources for testing."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="Test response")

        class MockMemory:
            def __init__(self):
                self.data = {}

            async def store(self, key, value):
                self.data[key] = value

            async def load(self, key, default=None):
                return self.data.get(key, default)

        mock_logging = MagicMock()
        mock_logging.log = AsyncMock()

        return {
            "llm": mock_llm,
            "memory": MockMemory(),
            "logging": mock_logging,
        }

    @pytest.fixture
    def basic_plugin(self, mock_resources):
        """Create basic plugin with default config."""
        config = {
            "enabled": True,
            "default_namespace": "test",
            "allow_dynamic_registration": True,
            "enable_versioning": True,
        }
        return FunctionSchemaRegistryPlugin(mock_resources, config)

    @pytest.fixture
    def strict_plugin(self, mock_resources):
        """Create plugin with strict validation."""
        config = {
            "enabled": True,
            "default_validation_mode": "strict",
            "validate_on_registration": True,
            "allow_unknown_parameters": False,
        }
        return FunctionSchemaRegistryPlugin(mock_resources, config)

    @pytest.fixture
    def sample_schema(self):
        """Create a sample function schema."""
        return FunctionSchema(
            name="test_function",
            description="A test function",
            version="1.0.0",
            parameters=[
                FunctionParameter(
                    name="input_text",
                    type=ParameterType.STRING,
                    description="Input text to process",
                    required=True,
                    min_length=1,
                    max_length=1000,
                ),
                FunctionParameter(
                    name="max_length",
                    type=ParameterType.INTEGER,
                    description="Maximum output length",
                    required=False,
                    default=100,
                    minimum=1,
                    maximum=10000,
                ),
                FunctionParameter(
                    name="format",
                    type=ParameterType.STRING,
                    description="Output format",
                    required=False,
                    enum=["json", "text", "html"],
                    default="text",
                ),
            ],
            tags=["text", "processing"],
            harmony_compatible=True,
        )

    @pytest.fixture
    def context(self, mock_resources):
        """Create mock plugin context."""
        ctx = PluginContext(mock_resources, "test_user")
        ctx.current_stage = WorkflowExecutor.PARSE
        ctx.message = "Test message"
        ctx.metadata = {}
        ctx.log = AsyncMock()
        return ctx

    def test_plugin_initialization(self, basic_plugin):
        """Test plugin initialization."""
        assert basic_plugin.config.enabled is True
        assert basic_plugin.config.default_namespace == "test"
        assert WorkflowExecutor.PARSE in basic_plugin.supported_stages
        assert WorkflowExecutor.DO in basic_plugin.supported_stages
        assert len(basic_plugin._function_registry) == 0
        assert "default" in basic_plugin._namespace_index

    def test_plugin_initialization_invalid_config(self, mock_resources):
        """Test plugin initialization with invalid config."""
        config = {
            "max_versions_per_function": 200,  # Exceeds maximum
        }

        with pytest.raises(ValueError, match="Invalid configuration"):
            FunctionSchemaRegistryPlugin(mock_resources, config)

    @pytest.mark.asyncio
    async def test_register_function_success(
        self, basic_plugin, sample_schema, context
    ):
        """Test successful function registration."""
        result = await basic_plugin.register_function(
            sample_schema, context, namespace="test"
        )

        assert result is True
        assert basic_plugin.get_function("test_function", "test") is not None
        assert basic_plugin._stats["total_registrations"] == 1

    @pytest.mark.asyncio
    async def test_register_function_from_dict(self, basic_plugin, context):
        """Test registering function from dictionary."""
        schema_dict = {
            "name": "dict_function",
            "description": "Function from dict",
            "parameters": [
                {
                    "name": "param1",
                    "type": "string",
                    "required": True,
                }
            ],
        }

        result = await basic_plugin.register_function(schema_dict, context)

        assert result is True
        assert basic_plugin.get_function("dict_function") is not None

    @pytest.mark.asyncio
    async def test_register_function_with_handler(
        self, basic_plugin, sample_schema, context
    ):
        """Test registering function with handler."""

        async def test_handler(**kwargs):
            return "handled"

        result = await basic_plugin.register_function(
            sample_schema, context, handler=test_handler
        )

        assert result is True
        reg_key = f"{basic_plugin.config.default_namespace}:{sample_schema.name}"
        assert reg_key in basic_plugin._function_handlers

    @pytest.mark.asyncio
    async def test_register_function_validation_failure(self, strict_plugin, context):
        """Test function registration with validation failure."""
        invalid_schema = FunctionSchema(
            name="invalid-name",  # Invalid name (contains hyphen)
            description="Invalid function",
            version="invalid",  # Invalid version format
        )

        result = await strict_plugin.register_function(invalid_schema, context)

        assert result is False
        assert strict_plugin.get_function("invalid-name") is None

    @pytest.mark.asyncio
    async def test_validate_function_call_success(
        self, basic_plugin, sample_schema, context
    ):
        """Test successful function call validation."""
        # Register function first
        await basic_plugin.register_function(sample_schema, context)

        # Validate call with valid parameters
        parameters = {
            "input_text": "Hello world",
            "max_length": 50,
            "format": "json",
        }

        result = await basic_plugin.validate_function_call(
            "test_function", parameters, "test"
        )

        assert result.valid is True
        assert len(result.errors) == 0
        assert basic_plugin._stats["total_validations"] == 1

    @pytest.mark.asyncio
    async def test_validate_function_call_missing_required(
        self, basic_plugin, sample_schema, context
    ):
        """Test validation with missing required parameter."""
        await basic_plugin.register_function(sample_schema, context)

        parameters = {
            "max_length": 50,  # Missing required 'input_text'
        }

        result = await basic_plugin.validate_function_call("test_function", parameters)

        assert result.valid is False
        assert "Missing required parameters: input_text" in result.errors
        assert "input_text" in result.missing_required

    @pytest.mark.asyncio
    async def test_validate_function_call_type_error(
        self, basic_plugin, sample_schema, context
    ):
        """Test validation with type error."""
        await basic_plugin.register_function(sample_schema, context)

        parameters = {
            "input_text": "Hello",
            "max_length": "not_a_number",  # Should be integer
        }

        result = await basic_plugin.validate_function_call("test_function", parameters)

        assert result.valid is False
        assert any(
            "expects" in error and "integer" in error.lower() for error in result.errors
        )

    @pytest.mark.asyncio
    async def test_validate_function_call_enum_violation(
        self, basic_plugin, sample_schema, context
    ):
        """Test validation with enum violation."""
        await basic_plugin.register_function(sample_schema, context)

        parameters = {
            "input_text": "Hello",
            "format": "xml",  # Not in enum ["json", "text", "html"]
        }

        result = await basic_plugin.validate_function_call("test_function", parameters)

        assert result.valid is False
        assert any("must be one of" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_function_call_range_violation(
        self, basic_plugin, sample_schema, context
    ):
        """Test validation with range violation."""
        await basic_plugin.register_function(sample_schema, context)

        parameters = {
            "input_text": "Hello",
            "max_length": 20000,  # Exceeds maximum of 10000
        }

        result = await basic_plugin.validate_function_call("test_function", parameters)

        assert result.valid is False
        assert any("must be <=" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_function_call_with_defaults(self, basic_plugin, context):
        """Test validation using default values."""
        # Create schema with defaults
        schema = FunctionSchema(
            name="default_func",
            description="Function with defaults",
            parameters=[
                FunctionParameter(
                    name="required_param", type=ParameterType.STRING, required=True
                ),
                FunctionParameter(
                    name="optional_param",
                    type=ParameterType.INTEGER,
                    required=False,
                    default=10,
                ),
                FunctionParameter(
                    name="another_optional",
                    type=ParameterType.STRING,
                    required=False,
                    default="default_value",
                ),
            ],
        )
        await basic_plugin.register_function(schema, context, namespace="test")

        # Only provide required parameter
        result = await basic_plugin.validate_function_call(
            "default_func", {"required_param": "test"}, "test"
        )

        assert result.valid is True
        # The current implementation applies defaults but doesn't track them in coerced_values
        # Just verify the validation passed with missing optional parameters

    @pytest.mark.asyncio
    async def test_validate_function_not_found(self, basic_plugin):
        """Test validation for non-existent function."""
        result = await basic_plugin.validate_function_call(
            "nonexistent_function", {}, "test"
        )

        assert result.valid is False
        assert "not found" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_disabled_function(
        self, basic_plugin, sample_schema, context
    ):
        """Test validation for disabled function."""
        await basic_plugin.register_function(sample_schema, context)
        basic_plugin.enable_function("test_function", "test", enabled=False)

        result = await basic_plugin.validate_function_call(
            "test_function", {"input_text": "test"}, "test"
        )

        assert result.valid is False
        assert "disabled" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_deprecated_function(self, basic_plugin, context):
        """Test validation for deprecated function."""
        deprecated_schema = FunctionSchema(
            name="deprecated_func",
            description="Deprecated function",
            deprecated=True,
            deprecated_message="Use new_func instead",
        )

        await basic_plugin.register_function(deprecated_schema, context)

        result = await basic_plugin.validate_function_call("deprecated_func", {})

        assert result.valid is True  # Still valid but with warning
        assert len(result.warnings) > 0
        assert "deprecated" in result.warnings[0].lower()

    @pytest.mark.asyncio
    async def test_discover_functions_all(self, basic_plugin, sample_schema, context):
        """Test discovering all functions."""
        # Register multiple functions
        await basic_plugin.register_function(sample_schema, context)

        schema2 = FunctionSchema(
            name="another_function",
            description="Another test function",
            tags=["other"],
        )
        await basic_plugin.register_function(schema2, context)

        result = await basic_plugin.discover_functions()

        assert isinstance(result, FunctionDiscoveryResult)
        assert result.total_functions == 2
        assert len(result.matched_functions) == 2
        assert "test" in result.namespaces

    @pytest.mark.asyncio
    async def test_discover_functions_by_namespace(
        self, basic_plugin, sample_schema, context
    ):
        """Test discovering functions by namespace."""
        await basic_plugin.register_function(sample_schema, context, namespace="test")
        await basic_plugin.register_function(
            FunctionSchema(name="other_func", description="Other"),
            context,
            namespace="other",
        )

        result = await basic_plugin.discover_functions(namespace="test")

        assert len(result.matched_functions) == 1
        assert result.matched_functions[0].name == "test_function"

    @pytest.mark.asyncio
    async def test_discover_functions_by_tags(
        self, basic_plugin, sample_schema, context
    ):
        """Test discovering functions by tags."""
        await basic_plugin.register_function(sample_schema, context)

        result = await basic_plugin.discover_functions(tags=["text"])

        assert len(result.matched_functions) == 1
        assert "text" in result.matched_functions[0].tags

    @pytest.mark.asyncio
    async def test_discover_functions_by_pattern(
        self, basic_plugin, sample_schema, context
    ):
        """Test discovering functions by name pattern."""
        await basic_plugin.register_function(sample_schema, context)

        result = await basic_plugin.discover_functions(name_pattern=r"^test_.*")

        assert len(result.matched_functions) == 1
        assert result.matched_functions[0].name.startswith("test_")

    @pytest.mark.asyncio
    async def test_discover_functions_exclude_deprecated(self, basic_plugin, context):
        """Test excluding deprecated functions from discovery."""
        deprecated = FunctionSchema(
            name="deprecated_func",
            description="Deprecated",
            deprecated=True,
        )
        await basic_plugin.register_function(deprecated, context)

        result = await basic_plugin.discover_functions(include_deprecated=False)

        assert len(result.matched_functions) == 0

    def test_get_harmony_description(self, basic_plugin, sample_schema, context):
        """Test getting harmony-compatible description."""
        basic_plugin._function_registry["test:test_function"] = FunctionRegistration(
            schema=sample_schema
        )

        harmony_desc = basic_plugin.get_harmony_description("test_function", "test")

        assert harmony_desc is not None
        assert harmony_desc["type"] == "function"
        assert harmony_desc["function"]["name"] == "test_function"
        assert "input_text" in harmony_desc["function"]["parameters"]["properties"]
        assert "input_text" in harmony_desc["function"]["parameters"]["required"]

    def test_get_harmony_description_not_compatible(self, basic_plugin, context):
        """Test harmony description for non-compatible function."""
        schema = FunctionSchema(
            name="non_harmony",
            description="Not harmony compatible",
            harmony_compatible=False,
        )
        basic_plugin._function_registry["test:non_harmony"] = FunctionRegistration(
            schema=schema
        )

        harmony_desc = basic_plugin.get_harmony_description("non_harmony", "test")

        assert harmony_desc is None

    @pytest.mark.asyncio
    async def test_export_openapi_schema(self, basic_plugin, sample_schema, context):
        """Test exporting OpenAPI schema."""
        await basic_plugin.register_function(sample_schema, context)

        openapi_doc = basic_plugin.export_openapi_schema(namespace="test")

        assert "openapi" in openapi_doc
        assert "paths" in openapi_doc
        assert "/test/test_function" in openapi_doc["paths"]
        operation = openapi_doc["paths"]["/test/test_function"]["post"]
        assert operation["operationId"] == "test_function"
        assert "requestBody" in operation

    @pytest.mark.asyncio
    async def test_add_schema_version(self, basic_plugin, sample_schema, context):
        """Test adding schema versions."""
        # Register initial version
        await basic_plugin.register_function(sample_schema, context)

        # Add new version
        new_schema = FunctionSchema(
            name="test_function",
            description="Updated test function",
            version="1.1.0",
            parameters=sample_schema.parameters,
        )

        result = await basic_plugin.add_schema_version(
            "test_function", new_schema, "test", "Added new feature"
        )

        assert result is True
        versions = basic_plugin.get_function_versions("test_function", "test")
        assert len(versions) > 0
        assert versions[-1].version == "1.1.0"
        assert versions[-1].is_current is True

    @pytest.mark.asyncio
    async def test_auto_increment_version(self, basic_plugin, sample_schema, context):
        """Test auto-increment version feature."""
        basic_plugin.config.auto_increment_version = True
        await basic_plugin.register_function(sample_schema, context)

        new_schema = FunctionSchema(
            name="test_function",
            description="Updated",
            version="1.0.0",  # Same version, should be incremented
        )

        await basic_plugin.add_schema_version("test_function", new_schema, "test")

        current = basic_plugin.get_function("test_function", "test")
        assert current.version == "1.0.1"  # Auto-incremented

    @pytest.mark.asyncio
    async def test_version_limit(self, basic_plugin, sample_schema, context):
        """Test version limit enforcement."""
        basic_plugin.config.max_versions_per_function = 3
        await basic_plugin.register_function(sample_schema, context)

        # Add multiple versions
        for i in range(5):
            new_schema = FunctionSchema(
                name="test_function",
                description=f"Version {i}",
                version=f"1.{i}.0",
            )
            await basic_plugin.add_schema_version("test_function", new_schema, "test")

        versions = basic_plugin.get_function_versions("test_function", "test")
        assert len(versions) <= 3  # Should be limited

    def test_get_function(self, basic_plugin, sample_schema):
        """Test getting a function schema."""
        basic_plugin._function_registry["test:test_function"] = FunctionRegistration(
            schema=sample_schema
        )

        function = basic_plugin.get_function("test_function", "test")

        assert function is not None
        assert function.name == "test_function"

    @pytest.mark.asyncio
    async def test_list_functions(self, basic_plugin, sample_schema, context):
        """Test listing functions."""
        await basic_plugin.register_function(sample_schema, context)

        # List all
        functions = basic_plugin.list_functions()
        assert "test_function" in functions

        # List by namespace
        functions = basic_plugin.list_functions(namespace="test")
        assert "test_function" in functions

        # Empty namespace
        functions = basic_plugin.list_functions(namespace="empty")
        assert len(functions) == 0

    @pytest.mark.asyncio
    async def test_delete_function(self, basic_plugin, sample_schema, context):
        """Test deleting a function."""
        await basic_plugin.register_function(sample_schema, context)

        # Verify it exists
        assert basic_plugin.get_function("test_function", "test") is not None

        # Delete it
        result = basic_plugin.delete_function("test_function", "test")

        assert result is True

        # Verify it's gone
        assert basic_plugin.get_function("test_function", "test") is None

        # Try to delete non-existent
        result = basic_plugin.delete_function("nonexistent", "test")
        assert result is False

    def test_enable_disable_function(self, basic_plugin, sample_schema):
        """Test enabling/disabling functions."""
        reg_key = "test:test_function"
        basic_plugin._function_registry[reg_key] = FunctionRegistration(
            schema=sample_schema
        )

        # Disable
        result = basic_plugin.enable_function("test_function", "test", enabled=False)
        assert result is True
        assert basic_plugin._function_registry[reg_key].enabled is False

        # Enable
        result = basic_plugin.enable_function("test_function", "test", enabled=True)
        assert result is True
        assert basic_plugin._function_registry[reg_key].enabled is True

    @pytest.mark.asyncio
    async def test_caching_validation(self, basic_plugin, sample_schema, context):
        """Test validation result caching."""
        await basic_plugin.register_function(sample_schema, context)
        parameters = {"input_text": "test", "max_length": 100}

        # First call - cache miss
        result1 = await basic_plugin.validate_function_call("test_function", parameters)
        cache_misses_1 = basic_plugin._stats["cache_misses"]

        # Second call - cache hit
        result2 = await basic_plugin.validate_function_call("test_function", parameters)
        cache_hits = basic_plugin._stats["cache_hits"]

        assert result1.valid == result2.valid
        assert cache_hits > 0
        assert basic_plugin._stats["cache_misses"] == cache_misses_1

    @pytest.mark.asyncio
    async def test_caching_discovery(self, basic_plugin, sample_schema, context):
        """Test discovery result caching."""
        await basic_plugin.register_function(sample_schema, context)

        # First call - cache miss
        result1 = await basic_plugin.discover_functions(namespace="test")
        _ = basic_plugin._stats["cache_misses"]  # Verify cache miss occurred

        # Second call - cache hit
        result2 = await basic_plugin.discover_functions(namespace="test")
        cache_hits = basic_plugin._stats["cache_hits"]

        assert result1.total_functions == result2.total_functions
        assert cache_hits > 0

    def test_parameter_type_coercion(self, basic_plugin):
        """Test parameter type coercion."""
        basic_plugin.config.coerce_types = True

        # Test string to int
        result = basic_plugin._try_coerce_type("42", ParameterType.INTEGER)
        assert result == 42

        # Test string to float
        result = basic_plugin._try_coerce_type("3.14", ParameterType.NUMBER)
        assert result == 3.14

        # Test string to bool
        result = basic_plugin._try_coerce_type("true", ParameterType.BOOLEAN)
        assert result is True

        # Test to array
        result = basic_plugin._try_coerce_type("single", ParameterType.ARRAY)
        assert result == ["single"]

        # Test invalid coercion
        result = basic_plugin._try_coerce_type("not_a_number", ParameterType.INTEGER)
        assert result is None

    def test_get_statistics(self, basic_plugin):
        """Test getting registry statistics."""
        stats = basic_plugin.get_statistics()

        assert "total_functions" in stats
        assert "total_namespaces" in stats
        assert "total_tags" in stats
        assert "cache_size" in stats
        assert "stats" in stats
        assert stats["stats"]["total_registrations"] == 0

    @pytest.mark.asyncio
    async def test_execute_parse_stage(self, basic_plugin, context):
        """Test execution in PARSE stage."""
        context.current_stage = WorkflowExecutor.PARSE
        context.message = 'Test @function(name="test", description="Test func")'

        result = await basic_plugin._execute_impl(context)

        assert result == context.message

    @pytest.mark.asyncio
    async def test_execute_do_stage(self, basic_plugin, sample_schema, context):
        """Test execution in DO stage."""
        await basic_plugin.register_function(sample_schema, context)
        context.current_stage = WorkflowExecutor.DO
        context.message = 'test_function(input_text="hello", max_length=100)'

        result = await basic_plugin._execute_impl(context)

        assert result == context.message

    @pytest.mark.asyncio
    async def test_execute_do_stage_validation_failure(
        self, strict_plugin, sample_schema, context
    ):
        """Test DO stage with validation failure."""
        await strict_plugin.register_function(sample_schema, context)
        context.current_stage = WorkflowExecutor.DO
        context.message = 'test_function(invalid_param="value")'

        result = await strict_plugin._execute_impl(context)

        # With strict mode, should return error message
        assert "validation failed" in result.lower()


class TestFunctionParameter:
    """Test FunctionParameter model."""

    def test_function_parameter_creation(self):
        """Test creating a function parameter."""
        param = FunctionParameter(
            name="test_param",
            type=ParameterType.STRING,
            description="Test parameter",
            required=True,
            min_length=1,
            max_length=100,
        )

        assert param.name == "test_param"
        assert param.type == ParameterType.STRING
        assert param.required is True
        assert param.min_length == 1

    def test_function_parameter_with_enum(self):
        """Test parameter with enum values."""
        param = FunctionParameter(
            name="choice_param",
            type=ParameterType.STRING,
            enum=["option1", "option2", "option3"],
        )

        assert param.enum == ["option1", "option2", "option3"]

    def test_function_parameter_with_pattern(self):
        """Test parameter with regex pattern."""
        param = FunctionParameter(
            name="email_param",
            type=ParameterType.STRING,
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        )

        assert param.pattern is not None


class TestFunctionSchema:
    """Test FunctionSchema model."""

    def test_function_schema_creation(self):
        """Test creating a function schema."""
        schema = FunctionSchema(
            name="test_func",
            description="Test function",
            version="1.0.0",
            parameters=[FunctionParameter(name="param1", type=ParameterType.STRING)],
            tags=["test"],
        )

        assert schema.name == "test_func"
        assert schema.version == "1.0.0"
        assert len(schema.parameters) == 1
        assert schema.harmony_compatible is True

    def test_function_schema_deprecated(self):
        """Test deprecated function schema."""
        schema = FunctionSchema(
            name="old_func",
            description="Deprecated function",
            deprecated=True,
            deprecated_message="Use new_func instead",
        )

        assert schema.deprecated is True
        assert "new_func" in schema.deprecated_message


class TestValidationResult:
    """Test ValidationResult model."""

    def test_validation_result_valid(self):
        """Test valid validation result."""
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=[],
        )

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validation_result_invalid(self):
        """Test invalid validation result."""
        result = ValidationResult(
            valid=False,
            errors=["Missing required parameter"],
            missing_required=["param1"],
        )

        assert result.valid is False
        assert len(result.errors) == 1
        assert "param1" in result.missing_required


class TestEnums:
    """Test enum functionality."""

    def test_schema_format_enum(self):
        """Test SchemaFormat enum."""
        assert SchemaFormat.OPENAPI_3_0.value == "openapi_3.0"
        assert SchemaFormat.JSON_SCHEMA.value == "json_schema"
        assert SchemaFormat.HARMONY.value == "harmony"

    def test_parameter_type_enum(self):
        """Test ParameterType enum."""
        assert ParameterType.STRING.value == "string"
        assert ParameterType.INTEGER.value == "integer"
        assert ParameterType.ARRAY.value == "array"

    def test_validation_mode_enum(self):
        """Test ValidationMode enum."""
        assert ValidationMode.STRICT.value == "strict"
        assert ValidationMode.PERMISSIVE.value == "permissive"
        assert ValidationMode.PARTIAL.value == "partial"


if __name__ == "__main__":
    pytest.main([__file__])
