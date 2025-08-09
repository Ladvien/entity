"""Unit tests for Structured Output Validator Plugin."""

import json
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, Field, ValidationError

from entity.plugins.context import PluginContext
from entity.plugins.gpt_oss.structured_output import (
    SchemaValidationResult,
    StructuredOutputPlugin,
    StructuredOutputValidationError,
)
from entity.workflow.executor import WorkflowExecutor


# Test schema models
class SimpleUserModel(BaseModel):
    """Simple user model for testing."""
    
    name: str = Field(description="User's full name")
    age: int = Field(description="User's age in years", ge=0, le=150)
    email: str = Field(description="User's email address")


class NestedAddressModel(BaseModel):
    """Nested address model."""
    
    street: str
    city: str
    zipcode: str
    country: str = "USA"


class ComplexUserModel(BaseModel):
    """Complex user model with nested fields."""
    
    id: int = Field(description="Unique user ID")
    profile: SimpleUserModel
    addresses: List[NestedAddressModel] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    is_active: bool = True


class OptionalFieldsModel(BaseModel):
    """Model with optional fields."""
    
    required_field: str
    optional_field: Optional[str] = None
    default_value: int = 42


class TestStructuredOutputPlugin:
    """Test StructuredOutputPlugin functionality."""

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
    def simple_plugin(self, mock_resources):
        """Create plugin with simple schema for testing."""
        config = {
            "output_schema": SimpleUserModel,
            "strict_mode": True,
            "enable_regeneration": False,  # Disable for simpler testing
            "preserve_original_on_failure": False  # Fail hard for testing
        }
        return StructuredOutputPlugin(mock_resources, config)

    @pytest.fixture
    def complex_plugin(self, mock_resources):
        """Create plugin with complex schema for testing."""
        config = {
            "output_schema": ComplexUserModel,
            "strict_mode": True,
            "enable_regeneration": True,
            "max_regeneration_attempts": 2
        }
        return StructuredOutputPlugin(mock_resources, config)

    @pytest.fixture
    def no_schema_plugin(self, mock_resources):
        """Create plugin without schema (pass-through mode)."""
        config = {}
        return StructuredOutputPlugin(mock_resources, config)

    @pytest.fixture
    def context(self, mock_resources):
        """Create mock plugin context."""
        ctx = PluginContext(mock_resources, "test_user")
        ctx.current_stage = WorkflowExecutor.REVIEW
        ctx.message = "Test message"
        ctx.get_resource = lambda name: mock_resources.get(name)
        return ctx

    def test_plugin_initialization(self, simple_plugin):
        """Test plugin initialization."""
        assert simple_plugin.output_schema == SimpleUserModel
        assert simple_plugin.config.strict_mode is True
        assert simple_plugin.config.enable_regeneration is False
        assert WorkflowExecutor.REVIEW in simple_plugin.supported_stages

    def test_plugin_initialization_invalid_config(self, mock_resources):
        """Test plugin initialization with invalid config."""
        config = {"max_regeneration_attempts": -1}  # Invalid negative value
        
        with pytest.raises(ValueError, match="Invalid configuration"):
            StructuredOutputPlugin(mock_resources, config)

    @pytest.mark.asyncio
    async def test_no_schema_passthrough(self, no_schema_plugin, context):
        """Test plugin passes through when no schema configured."""
        context.message = "Any message content"
        
        result = await no_schema_plugin._execute_impl(context)
        
        assert result == "Any message content"

    @pytest.mark.asyncio
    async def test_valid_simple_output(self, simple_plugin, context):
        """Test validation of valid simple output."""
        valid_json = json.dumps({
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        })
        context.message = valid_json
        
        result = await simple_plugin._execute_impl(context)
        
        # Should return formatted JSON
        parsed_result = json.loads(result)
        assert parsed_result["name"] == "John Doe"
        assert parsed_result["age"] == 30
        assert parsed_result["email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_invalid_json_output(self, simple_plugin, context):
        """Test handling of invalid JSON output."""
        context.message = "This is not JSON"
        
        with pytest.raises(StructuredOutputValidationError) as exc_info:
            await simple_plugin._execute_impl(context)
        
        # Since regeneration is disabled and preserve_original_on_failure is False,
        # it should fail with regeneration limit exceeded message
        assert ("Schema validation failed" in str(exc_info.value) or 
                "not valid JSON" in str(exc_info.value.validation_errors))

    @pytest.mark.asyncio
    async def test_schema_validation_failure(self, simple_plugin, context):
        """Test handling of schema validation failure."""
        invalid_json = json.dumps({
            "name": "John Doe",
            "age": "thirty",  # Should be int
            "email": "invalid-email"
        })
        context.message = invalid_json
        
        with pytest.raises(StructuredOutputValidationError) as exc_info:
            await simple_plugin._execute_impl(context)
        
        assert "Schema validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, simple_plugin, context):
        """Test handling of missing required fields."""
        incomplete_json = json.dumps({
            "name": "John Doe"
            # Missing age and email
        })
        context.message = incomplete_json
        
        with pytest.raises(StructuredOutputValidationError) as exc_info:
            await simple_plugin._execute_impl(context)
        
        assert "Schema validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complex_nested_validation_success(self, complex_plugin, context):
        """Test validation of complex nested schema."""
        complex_json = json.dumps({
            "id": 123,
            "profile": {
                "name": "Jane Smith",
                "age": 28,
                "email": "jane@example.com"
            },
            "addresses": [
                {
                    "street": "123 Main St",
                    "city": "Anytown", 
                    "zipcode": "12345",
                    "country": "USA"
                }
            ],
            "metadata": {"role": "admin"},
            "is_active": True
        })
        context.message = complex_json
        
        result = await complex_plugin._execute_impl(context)
        
        parsed_result = json.loads(result)
        assert parsed_result["id"] == 123
        assert parsed_result["profile"]["name"] == "Jane Smith"
        assert len(parsed_result["addresses"]) == 1

    @pytest.mark.asyncio
    async def test_complex_nested_validation_failure(self, complex_plugin, context):
        """Test validation failure with complex nested schema."""
        invalid_complex_json = json.dumps({
            "id": "not-a-number",  # Should be int
            "profile": {
                "name": "Jane Smith",
                "age": -5,  # Invalid age
                "email": "jane@example.com"
            }
        })
        context.message = invalid_complex_json
        
        with pytest.raises(StructuredOutputValidationError) as exc_info:
            await complex_plugin._execute_impl(context)
        
        error_message = str(exc_info.value)
        assert "Schema validation failed" in error_message

    @pytest.mark.asyncio
    async def test_regeneration_attempt_tracking(self, mock_resources):
        """Test regeneration attempt tracking."""
        config = {
            "output_schema": SimpleUserModel,
            "enable_regeneration": True,
            "max_regeneration_attempts": 2
        }
        plugin = StructuredOutputPlugin(mock_resources, config)
        context = PluginContext(mock_resources, "test_user")
        context.current_stage = WorkflowExecutor.REVIEW
        context.message = "Invalid JSON"
        
        # First attempt should increment counter
        with pytest.raises(StructuredOutputValidationError):
            await plugin._execute_impl(context)
        
        attempt_count = await context.recall("structured_output_attempts", 0)
        assert attempt_count == 1

    @pytest.mark.asyncio
    async def test_preserve_original_on_failure(self, mock_resources, context):
        """Test preserving original output when validation fails."""
        config = {
            "output_schema": SimpleUserModel,
            "enable_regeneration": False,
            "preserve_original_on_failure": True
        }
        plugin = StructuredOutputPlugin(mock_resources, config)
        context.message = "Invalid output"
        
        result = await plugin._execute_impl(context)
        
        assert result == "Invalid output"

    @pytest.mark.asyncio
    async def test_fail_hard_on_validation_error(self, mock_resources, context):
        """Test hard failure when preserve_original_on_failure is False."""
        config = {
            "output_schema": SimpleUserModel,
            "enable_regeneration": False,
            "preserve_original_on_failure": False
        }
        plugin = StructuredOutputPlugin(mock_resources, config)
        context.message = "Invalid output"
        
        with pytest.raises(StructuredOutputValidationError):
            await plugin._execute_impl(context)

    @pytest.mark.asyncio 
    async def test_validation_result_structure(self, simple_plugin):
        """Test validation result structure."""
        # Valid output
        valid_output = json.dumps({"name": "John", "age": 30, "email": "john@test.com"})
        result = await simple_plugin._validate_output(valid_output)
        
        assert result.valid is True
        assert result.validated_data is not None
        assert result.errors == []
        
        # Invalid output
        invalid_output = json.dumps({"name": "John", "age": "thirty"})
        result = await simple_plugin._validate_output(invalid_output)
        
        assert result.valid is False
        assert result.validated_data is None
        assert len(result.errors) > 0

    def test_regeneration_prompt_creation(self, simple_plugin):
        """Test regeneration prompt creation."""
        errors = ["age: Input should be a valid integer", "email: Field required"]
        original_output = '{"name": "John", "age": "thirty"}'
        
        prompt = simple_plugin._create_regeneration_prompt(errors, original_output)
        
        assert "age: Input should be a valid integer" in prompt
        assert "email: Field required" in prompt
        assert original_output in prompt
        assert "schema" in prompt.lower()

    def test_dynamic_schema_setting(self, no_schema_plugin):
        """Test dynamic schema setting."""
        assert no_schema_plugin.output_schema is None
        
        no_schema_plugin.set_schema(SimpleUserModel)
        
        assert no_schema_plugin.output_schema == SimpleUserModel
        assert no_schema_plugin.config.output_schema == SimpleUserModel

    def test_get_schema_info(self, simple_plugin, no_schema_plugin):
        """Test schema info retrieval."""
        # Plugin with schema
        info = simple_plugin.get_schema_info()
        assert info["schema_configured"] is True
        assert info["schema_name"] == "SimpleUserModel"
        assert "schema_json" in info
        
        # Plugin without schema
        info = no_schema_plugin.get_schema_info()
        assert info["schema_configured"] is False

    @pytest.mark.asyncio
    async def test_standalone_validation(self, simple_plugin):
        """Test standalone validation method."""
        valid_json = json.dumps({"name": "John", "age": 30, "email": "john@test.com"})
        
        result = await simple_plugin.validate_standalone(valid_json)
        
        assert result.valid is True
        assert result.validated_data is not None

    @pytest.mark.asyncio
    async def test_optional_fields_model(self, mock_resources):
        """Test validation with optional fields."""
        config = {"output_schema": OptionalFieldsModel}
        plugin = StructuredOutputPlugin(mock_resources, config)
        
        # Valid with only required field
        minimal_json = json.dumps({"required_field": "test"})
        
        # This should pass validation
        result = await plugin._validate_output(minimal_json)
        assert result.valid is True

    @pytest.mark.asyncio
    async def test_error_logging(self, simple_plugin, context):
        """Test that validation errors are properly logged."""
        context.message = "Invalid JSON"
        
        try:
            await simple_plugin._execute_impl(context)
        except StructuredOutputValidationError:
            pass  # Expected
        
        # Verify logging was called
        logger = context.get_resource("logging")
        logger.log.assert_called()

    @pytest.mark.asyncio
    async def test_success_logging(self, simple_plugin, context):
        """Test that successful validation is logged."""
        valid_json = json.dumps({"name": "John", "age": 30, "email": "john@test.com"})
        context.message = valid_json
        
        await simple_plugin._execute_impl(context)
        
        # Verify success logging
        logger = context.get_resource("logging") 
        logger.log.assert_called()

    @pytest.mark.asyncio
    async def test_attempt_counter_reset_on_success(self, mock_resources, context):
        """Test that attempt counter is reset on successful validation."""
        config = {
            "output_schema": SimpleUserModel,
            "enable_regeneration": True
        }
        plugin = StructuredOutputPlugin(mock_resources, config)
        
        # Set initial attempt count
        await context.remember("structured_output_attempts", 2)
        
        # Successful validation
        valid_json = json.dumps({"name": "John", "age": 30, "email": "john@test.com"})
        context.message = valid_json
        
        await plugin._execute_impl(context)
        
        # Attempt count should be reset
        attempt_count = await context.recall("structured_output_attempts", 0)
        assert attempt_count == 0

    def test_supported_stages(self, simple_plugin):
        """Test that plugin only supports REVIEW stage."""
        assert simple_plugin.supported_stages == [WorkflowExecutor.REVIEW]

    def test_required_dependencies(self, simple_plugin):
        """Test that plugin declares correct dependencies."""
        assert "llm" in simple_plugin.dependencies
        assert "memory" in simple_plugin.dependencies

    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self, mock_resources, context):
        """Test handling of unexpected errors during validation."""
        # Create a plugin that will cause an unexpected error
        config = {"output_schema": SimpleUserModel, "preserve_original_on_failure": True}
        plugin = StructuredOutputPlugin(mock_resources, config)
        
        # Mock the validation method to raise an unexpected error
        original_validate = plugin._validate_output
        
        async def mock_validate(output):
            raise RuntimeError("Unexpected error")
        
        plugin._validate_output = mock_validate
        context.message = "test"
        
        # Should handle the error gracefully
        result = await plugin._execute_impl(context)
        assert result == "test"  # Original message preserved

    def test_model_classes(self):
        """Test Pydantic model classes used in tests."""
        # Test SimpleUserModel
        simple = SimpleUserModel(name="John", age=30, email="john@test.com")
        assert simple.name == "John"
        assert simple.age == 30
        
        # Test validation
        with pytest.raises(ValidationError):
            SimpleUserModel(name="John", age=-1, email="invalid")  # Age validation should fail
        
        # Test ComplexUserModel
        profile = SimpleUserModel(name="Jane", age=25, email="jane@test.com")
        address = NestedAddressModel(street="123 Main", city="Town", zipcode="12345")
        
        complex_user = ComplexUserModel(id=1, profile=profile, addresses=[address])
        assert complex_user.id == 1
        assert complex_user.profile.name == "Jane"
        assert len(complex_user.addresses) == 1

    def test_schema_validation_result_model(self):
        """Test SchemaValidationResult model."""
        # Success result
        success_result = SchemaValidationResult(
            valid=True,
            validated_data={"test": "data"}
        )
        assert success_result.valid is True
        assert success_result.errors == []
        
        # Failure result
        failure_result = SchemaValidationResult(
            valid=False,
            errors=["Error 1", "Error 2"],
            original_output="bad output"
        )
        assert failure_result.valid is False
        assert len(failure_result.errors) == 2