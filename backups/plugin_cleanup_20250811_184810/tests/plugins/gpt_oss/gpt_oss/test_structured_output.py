"""Tests for Structured Output Validator Plugin."""

import json
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from entity.plugins.context import PluginContext
from entity.plugins.gpt_oss import StructuredOutputPlugin, ValidationResult
from entity.workflow.executor import WorkflowExecutor


class DemoOutputModel(BaseModel):
    """Test Pydantic model for structured output."""

    name: str
    age: int
    email: Optional[str] = None
    is_active: bool = True


class NestedOutputModel(BaseModel):
    """Test nested Pydantic model."""

    class PersonModel(BaseModel):
        name: str
        age: int

    class CompanyModel(BaseModel):
        name: str
        employees: list["PersonModel"]

    user: PersonModel
    company: CompanyModel
    metadata: Dict[str, Any]


@pytest.fixture
def mock_resources():
    """Create mock resources for testing."""
    resources = MagicMock()
    llm_resource = AsyncMock()
    llm_resource.generate = AsyncMock(return_value='{"name": "John", "age": 30}')
    resources.get.return_value = llm_resource
    return resources


@pytest.fixture
def mock_context():
    """Create mock plugin context for testing."""
    context = MagicMock(spec=PluginContext)
    context.user_id = "test_user"
    context.message = '{"name": "John", "age": 30}'
    context.resources = MagicMock()
    return context


@pytest.fixture
def plugin_config():
    """Create plugin configuration for testing."""
    return StructuredOutputPlugin.ConfigModel(
        output_schema=DemoOutputModel, strict_mode=True, max_regeneration_attempts=2
    )


@pytest.fixture
def json_schema_config():
    """Create JSON schema configuration for testing."""
    return StructuredOutputPlugin.ConfigModel(
        schema_dict={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string"},
                "is_active": {"type": "boolean"},
            },
            "required": ["name", "age"],
        },
        strict_mode=True,
    )


class TestStructuredOutputPlugin:
    """Test cases for StructuredOutputPlugin."""

    def test_plugin_initialization(self, mock_resources, plugin_config):
        """Test plugin initialization with valid configuration."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)

        assert plugin.supported_stages == [WorkflowExecutor.REVIEW]
        assert plugin.config.output_schema == DemoOutputModel
        assert plugin.config.strict_mode is True
        assert plugin.config.max_regeneration_attempts == 2

    def test_plugin_initialization_no_schema_error(self, mock_resources):
        """Test plugin initialization fails without schema configuration."""
        config = StructuredOutputPlugin.ConfigModel()

        with pytest.raises(
            ValueError, match="Either output_schema or schema_dict must be provided"
        ):
            StructuredOutputPlugin(mock_resources, config)

    def test_plugin_initialization_with_json_schema(
        self, mock_resources, json_schema_config
    ):
        """Test plugin initialization with JSON schema configuration."""
        plugin = StructuredOutputPlugin(mock_resources, json_schema_config)

        assert plugin.config.schema_dict is not None
        assert plugin.config.output_schema is None

    @pytest.mark.asyncio
    async def test_execute_valid_output(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test execution with valid JSON output."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        mock_context.message = (
            '{"name": "John", "age": 30, "email": "john@example.com"}'
        )

        result = await plugin._execute_impl(mock_context)

        # Should return validated JSON
        parsed_result = json.loads(result)
        assert parsed_result["name"] == "John"
        assert parsed_result["age"] == 30
        assert parsed_result["email"] == "john@example.com"
        assert parsed_result["is_active"] is True  # Default value

    @pytest.mark.asyncio
    async def test_execute_invalid_json_format(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test execution with invalid JSON format."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        mock_context.message = "This is not valid JSON"

        # Mock the LLM resource for regeneration
        mock_resources.get.return_value.generate.return_value = (
            '{"name": "Fixed", "age": 25}'
        )

        with patch.object(plugin, "_handle_regeneration") as mock_regen:
            mock_regen.return_value = '{"name": "Fixed", "age": 25}'

            result = await plugin._execute_impl(mock_context)

            mock_regen.assert_called_once()
            assert "Fixed" in result

    @pytest.mark.asyncio
    async def test_execute_validation_error_strict_mode(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test execution with validation error in strict mode."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        mock_context.message = '{"name": "John"}'  # Missing required 'age' field

        # Mock regeneration to return valid data
        with patch.object(plugin, "_handle_regeneration") as mock_regen:
            mock_regen.return_value = '{"name": "John", "age": 30}'

            await plugin._execute_impl(mock_context)

            mock_regen.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_validation_error_non_strict_mode(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test execution with validation error in non-strict mode."""
        plugin_config.strict_mode = False
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        mock_context.message = '{"name": "John"}'  # Missing required 'age' field

        result = await plugin._execute_impl(mock_context)

        # Should return original message in non-strict mode
        assert result == mock_context.message

    @pytest.mark.asyncio
    async def test_validate_output_success(self, mock_resources, plugin_config):
        """Test successful output validation."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        output = '{"name": "Alice", "age": 25, "email": "alice@example.com"}'

        result = await plugin._validate_output(output)

        assert result.is_valid is True
        assert result.validated_data is not None
        assert result.errors is None
        assert result.regeneration_needed is False

    @pytest.mark.asyncio
    async def test_validate_output_json_error(self, mock_resources, plugin_config):
        """Test validation with JSON decode error."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        output = "This is not JSON"

        result = await plugin._validate_output(output)

        assert result.is_valid is False
        assert result.validated_data is None
        assert "Invalid JSON format" in str(result.errors)
        assert result.regeneration_needed is True

    @pytest.mark.asyncio
    async def test_validate_output_schema_error(self, mock_resources, plugin_config):
        """Test validation with schema validation error."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        output = '{"name": "Bob", "age": "not_a_number"}'  # Invalid age type

        result = await plugin._validate_output(output)

        assert result.is_valid is False
        assert result.validated_data is None
        assert result.errors is not None
        assert result.regeneration_needed is True

    def test_extract_json_from_text_pure_json(self, mock_resources, plugin_config):
        """Test JSON extraction from pure JSON text."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        text = '{"name": "John", "age": 30}'

        result = plugin._extract_json_from_text(text)

        assert result == {"name": "John", "age": 30}

    def test_extract_json_from_text_code_block(self, mock_resources, plugin_config):
        """Test JSON extraction from markdown code block."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        text = """Here is the response:

```json
{"name": "John", "age": 30}
```

Hope this helps!"""

        result = plugin._extract_json_from_text(text)

        assert result == {"name": "John", "age": 30}

    def test_extract_json_from_text_embedded(self, mock_resources, plugin_config):
        """Test JSON extraction from text with embedded JSON."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        text = 'The data is {"name": "John", "age": 30} as requested.'

        result = plugin._extract_json_from_text(text)

        assert result == {"name": "John", "age": 30}

    def test_extract_json_from_text_no_json(self, mock_resources, plugin_config):
        """Test JSON extraction failure when no JSON present."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        text = "This text contains no JSON data."

        with pytest.raises(json.JSONDecodeError):
            plugin._extract_json_from_text(text)

    @pytest.mark.asyncio
    async def test_get_validation_schema_pydantic(self, mock_resources, plugin_config):
        """Test getting Pydantic validation schema."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)

        schema = await plugin._get_validation_schema()

        assert schema == DemoOutputModel

    @pytest.mark.asyncio
    async def test_get_validation_schema_json_dict(
        self, mock_resources, json_schema_config
    ):
        """Test getting JSON schema validation."""
        plugin = StructuredOutputPlugin(mock_resources, json_schema_config)

        schema = await plugin._get_validation_schema()

        # Should return a dynamically created Pydantic model
        assert hasattr(schema, "model_validate")
        assert hasattr(schema, "model_json_schema")

    def test_json_type_to_python_type_conversions(self, mock_resources, plugin_config):
        """Test JSON type to Python type conversions."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)

        assert plugin._json_type_to_python_type({"type": "string"}) is str
        assert plugin._json_type_to_python_type({"type": "integer"}) is int
        assert plugin._json_type_to_python_type({"type": "number"}) is float
        assert plugin._json_type_to_python_type({"type": "boolean"}) is bool
        assert plugin._json_type_to_python_type({"type": "array"}) is list
        assert plugin._json_type_to_python_type({"type": "object"}) is dict
        assert plugin._json_type_to_python_type({"type": "null"}) is type(None)
        assert plugin._json_type_to_python_type({"type": "unknown"}) is str

    @pytest.mark.asyncio
    async def test_handle_regeneration_success(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test successful output regeneration."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)

        validation_result = ValidationResult(
            is_valid=False,
            errors=["Missing required field: age"],
            raw_output='{"name": "John"}',
            regeneration_needed=True,
        )

        # Mock the regeneration process
        with patch.object(plugin, "_request_regeneration") as mock_request:
            mock_request.return_value = '{"name": "John", "age": 30}'

            result = await plugin._handle_regeneration(mock_context, validation_result)

            # Should return valid regenerated output
            parsed_result = json.loads(result)
            assert parsed_result["name"] == "John"
            assert parsed_result["age"] == 30

    @pytest.mark.asyncio
    async def test_handle_regeneration_max_attempts(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test regeneration failure after max attempts."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        plugin._regeneration_count = 2  # Already at max

        validation_result = ValidationResult(
            is_valid=False,
            errors=["Validation error"],
            raw_output="invalid",
            regeneration_needed=True,
        )

        with pytest.raises(ValueError, match="Max regeneration attempts"):
            await plugin._handle_regeneration(mock_context, validation_result)

    @pytest.mark.asyncio
    async def test_request_regeneration_with_llm(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test regeneration request with LLM resource."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)

        result = await plugin._request_regeneration(mock_context)

        mock_resources.get.assert_called_with("llm")
        mock_resources.get.return_value.generate.assert_called_once()
        assert result == '{"name": "John", "age": 30}'

    @pytest.mark.asyncio
    async def test_request_regeneration_no_llm(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test regeneration request without LLM resource."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)
        mock_resources.get.return_value = None  # No LLM resource

        result = await plugin._request_regeneration(mock_context)

        # Should return original message as fallback
        assert result == mock_context.message

    def test_create_regeneration_message(self, mock_resources, plugin_config):
        """Test creation of regeneration message."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)

        validation_result = ValidationResult(
            is_valid=False,
            errors=["Missing field: age", "Invalid type for name"],
            raw_output='{"name": 123}',
            regeneration_needed=True,
        )

        schema_info = {"type": "object", "properties": {"name": {"type": "string"}}}

        message = plugin._create_regeneration_message(validation_result, schema_info)

        assert "did not conform to the required schema" in message
        assert "Missing field: age" in message
        assert "Invalid type for name" in message
        assert '"name": 123' in message
        assert "REQUIRED SCHEMA:" in message

    @pytest.mark.asyncio
    async def test_should_execute_with_schema(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test should_execute returns True when schema is configured."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)

        result = await plugin._should_execute(mock_context)

        assert result is True

    @pytest.mark.asyncio
    async def test_should_execute_without_schema(self, mock_resources, mock_context):
        """Test should_execute returns False when no schema is configured."""
        config = StructuredOutputPlugin.ConfigModel(
            output_schema=None,
            schema_dict=None,
            strict_mode=False,  # Allow creation without schema for this test
        )

        # Patch the __init__ to skip validation for this test
        with patch.object(StructuredOutputPlugin, "__init__", lambda self, r, c: None):
            plugin = StructuredOutputPlugin.__new__(StructuredOutputPlugin)
            plugin.config = config
            plugin.resources = mock_resources

            result = await plugin._should_execute(mock_context)

            assert result is False

    def test_get_schema_info_pydantic(self, mock_resources, plugin_config):
        """Test getting schema info for Pydantic model."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)

        info = plugin.get_schema_info()

        assert info["type"] == "pydantic_model"
        assert info["model_name"] == "DemoOutputModel"
        assert "properties" in info["schema"]
        assert "name" in info["schema"]["properties"]
        assert "age" in info["schema"]["properties"]

    def test_get_schema_info_json_schema(self, mock_resources, json_schema_config):
        """Test getting schema info for JSON schema."""
        plugin = StructuredOutputPlugin(mock_resources, json_schema_config)

        info = plugin.get_schema_info()

        assert info["type"] == "json_schema"
        assert info["schema"] == json_schema_config.schema_dict

    @pytest.mark.asyncio
    async def test_nested_model_validation(self, mock_resources, mock_context):
        """Test validation with nested Pydantic models."""
        config = StructuredOutputPlugin.ConfigModel(
            output_schema=NestedOutputModel, strict_mode=True
        )
        plugin = StructuredOutputPlugin(mock_resources, config)

        valid_data = {
            "user": {"name": "John", "age": 30},
            "company": {
                "name": "Tech Corp",
                "employees": [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 35}],
            },
            "metadata": {"department": "Engineering", "level": "Senior"},
        }

        mock_context.message = json.dumps(valid_data)

        result = await plugin._execute_impl(mock_context)

        # Should successfully validate and return the structured data
        parsed_result = json.loads(result)
        assert parsed_result["user"]["name"] == "John"
        assert len(parsed_result["company"]["employees"]) == 2
        assert parsed_result["metadata"]["department"] == "Engineering"

    @pytest.mark.asyncio
    async def test_complex_json_extraction(self, mock_resources, plugin_config):
        """Test extraction of JSON from complex text with multiple JSON-like structures."""
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)

        complex_text = """
        Here's some analysis of the data:

        First, let me show you the user profile: {"invalid": "json" with syntax error}

        But the actual valid data is:
        ```json
        {"name": "John", "age": 30, "email": "john@example.com"}
        ```

        And here's some additional context.
        """

        result = plugin._extract_json_from_text(complex_text)

        assert result["name"] == "John"
        assert result["age"] == 30
        assert result["email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_plugin_with_custom_error_messages(
        self, mock_resources, mock_context
    ):
        """Test plugin with custom error messages configuration."""
        config = StructuredOutputPlugin.ConfigModel(
            output_schema=DemoOutputModel,
            strict_mode=True,
            custom_error_messages={
                "missing_field": "The required field {field} is missing",
                "invalid_type": "The field {field} has an invalid type",
            },
        )
        plugin = StructuredOutputPlugin(mock_resources, config)

        # Test that custom error messages are available in config
        assert "missing_field" in plugin.config.custom_error_messages
        assert "invalid_type" in plugin.config.custom_error_messages

    @pytest.mark.asyncio
    async def test_partial_match_mode(self, mock_resources, mock_context):
        """Test plugin with allow_partial_match configuration."""
        config = StructuredOutputPlugin.ConfigModel(
            output_schema=DemoOutputModel, strict_mode=False, allow_partial_match=True
        )
        plugin = StructuredOutputPlugin(mock_resources, config)

        # Partial data (missing some fields)
        mock_context.message = '{"name": "John"}'

        result = await plugin._execute_impl(mock_context)

        # Should return original message in non-strict mode
        assert result == mock_context.message

    @pytest.mark.asyncio
    async def test_validation_timeout_handling(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test validation timeout configuration."""
        plugin_config.validation_timeout = 1.0
        plugin = StructuredOutputPlugin(mock_resources, plugin_config)

        # Test that timeout configuration is properly set
        assert plugin.config.validation_timeout == 1.0

        # Mock a slow LLM response
        mock_resources.get.return_value.generate = AsyncMock()

        # The timeout would be handled in the actual LLM call
        await plugin._request_regeneration(mock_context)

        mock_resources.get.return_value.generate.assert_called_once_with(
            mock_context.message, user_id=mock_context.user_id, timeout=1.0
        )


class TestValidationResult:
    """Test cases for ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test ValidationResult creation with all fields."""
        result = ValidationResult(
            is_valid=True,
            validated_data='{"name": "John"}',
            errors=None,
            raw_output='{"name": "John"}',
            regeneration_needed=False,
        )

        assert result.is_valid is True
        assert result.validated_data == '{"name": "John"}'
        assert result.errors is None
        assert result.raw_output == '{"name": "John"}'
        assert result.regeneration_needed is False

    def test_validation_result_failure(self):
        """Test ValidationResult for validation failure."""
        result = ValidationResult(
            is_valid=False,
            validated_data=None,
            errors=["Missing field: age"],
            raw_output='{"name": "John"}',
            regeneration_needed=True,
        )

        assert result.is_valid is False
        assert result.validated_data is None
        assert "Missing field: age" in result.errors
        assert result.regeneration_needed is True


class TestConfigModel:
    """Test cases for StructuredOutputPlugin.ConfigModel."""

    def test_config_model_defaults(self):
        """Test ConfigModel default values."""
        config = StructuredOutputPlugin.ConfigModel(output_schema=DemoOutputModel)

        assert config.output_schema == DemoOutputModel
        assert config.schema_dict is None
        assert config.strict_mode is True
        assert config.max_regeneration_attempts == 3
        assert config.allow_partial_match is False
        assert config.extract_json_from_text is True
        assert config.custom_error_messages is None
        assert config.validation_timeout == 5.0

    def test_config_model_custom_values(self):
        """Test ConfigModel with custom values."""
        custom_messages = {"error": "Custom error message"}

        config = StructuredOutputPlugin.ConfigModel(
            output_schema=DemoOutputModel,
            strict_mode=False,
            max_regeneration_attempts=5,
            allow_partial_match=True,
            extract_json_from_text=False,
            custom_error_messages=custom_messages,
            validation_timeout=10.0,
        )

        assert config.strict_mode is False
        assert config.max_regeneration_attempts == 5
        assert config.allow_partial_match is True
        assert config.extract_json_from_text is False
        assert config.custom_error_messages == custom_messages
        assert config.validation_timeout == 10.0


if __name__ == "__main__":
    pytest.main([__file__])
