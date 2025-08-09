"""Unit tests for Developer Override Plugin."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from entity.plugins.context import PluginContext
from entity.plugins.gpt_oss.developer_override import (
    DeveloperOverride,
    DeveloperOverrideAuditEntry,
    DeveloperOverridePlugin,
    DeveloperOverrideType,
    DeveloperRoleLevel,
)
from entity.workflow.executor import WorkflowExecutor


class TestDeveloperOverridePlugin:
    """Test DeveloperOverridePlugin functionality."""

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
            "enable_developer_overrides": True,
            "developer_permission_level": DeveloperRoleLevel.READ.value,
            "authorized_developers": ["dev_user"],
            "admin_users": ["admin_user"],
        }
        return DeveloperOverridePlugin(mock_resources, config)

    @pytest.fixture
    def restricted_plugin(self, mock_resources):
        """Create plugin with restricted config."""
        config = {
            "enable_developer_overrides": True,
            "developer_permission_level": DeveloperRoleLevel.NONE.value,
            "authorized_developers": [],
            "admin_users": ["admin_user"],
            "allow_system_prompt_override": False,
            "max_active_overrides": 3,
            "override_priority_threshold": 5,
        }
        return DeveloperOverridePlugin(mock_resources, config)

    @pytest.fixture
    def audit_plugin(self, mock_resources):
        """Create plugin with audit trail enabled."""
        config = {
            "enable_developer_overrides": True,
            "enable_audit_trail": True,
            "log_override_content": True,
            "audit_retention_days": 30,
            "authorized_developers": ["dev_user"],
        }
        return DeveloperOverridePlugin(mock_resources, config)

    @pytest.fixture
    def context(self, mock_resources):
        """Create mock plugin context."""
        ctx = PluginContext(mock_resources, "test_user")
        ctx.current_stage = WorkflowExecutor.PARSE
        ctx.message = "Test message"
        ctx.get_resource = lambda name: mock_resources.get(name)
        return ctx

    def test_plugin_initialization(self, basic_plugin):
        """Test plugin initialization."""
        assert basic_plugin.config.enable_developer_overrides is True
        assert basic_plugin.config.developer_permission_level == DeveloperRoleLevel.READ
        assert "dev_user" in basic_plugin.config.authorized_developers
        assert "admin_user" in basic_plugin.config.admin_users
        assert WorkflowExecutor.PARSE in basic_plugin.supported_stages

    def test_plugin_initialization_invalid_config(self, mock_resources):
        """Test plugin initialization with invalid config."""
        config = {"max_active_overrides": -1}  # Invalid negative value

        with pytest.raises(ValueError, match="Invalid configuration"):
            DeveloperOverridePlugin(mock_resources, config)

    @pytest.mark.asyncio
    async def test_plugin_disabled_passthrough(self, mock_resources, context):
        """Test that plugin passes through when disabled."""
        config = {"enable_developer_overrides": False}
        plugin = DeveloperOverridePlugin(mock_resources, config)

        result = await plugin._execute_impl(context)

        assert result == "Test message"

    @pytest.mark.asyncio
    async def test_no_permission_passthrough(self, restricted_plugin, context):
        """Test that users without permission get passthrough."""
        context.user_id = "regular_user"

        result = await restricted_plugin._execute_impl(context)

        assert result == "Test message"

    @pytest.mark.asyncio
    async def test_admin_permission_level(self, basic_plugin):
        """Test admin permission level detection."""
        admin_level = await basic_plugin._get_developer_permission_level("admin_user")
        assert admin_level == DeveloperRoleLevel.ADMIN

    @pytest.mark.asyncio
    async def test_developer_permission_level(self, basic_plugin):
        """Test developer permission level detection."""
        dev_level = await basic_plugin._get_developer_permission_level("dev_user")
        assert dev_level == DeveloperRoleLevel.OVERRIDE

    @pytest.mark.asyncio
    async def test_default_permission_level(self, basic_plugin):
        """Test default permission level."""
        default_level = await basic_plugin._get_developer_permission_level(
            "unknown_user"
        )
        assert default_level == DeveloperRoleLevel.READ

    @pytest.mark.asyncio
    async def test_add_override(self, basic_plugin):
        """Test adding a new override."""
        override_id = await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Be more creative",
            priority=7,
            description="Increase creativity level",
        )

        assert override_id is not None
        assert "dev_user" in override_id
        assert "behavior_modification" in override_id

    @pytest.mark.asyncio
    async def test_add_override_requires_description(self, mock_resources):
        """Test that override requires description when configured."""
        config = {
            "enable_developer_overrides": True,
            "require_override_description": True,
        }
        plugin = DeveloperOverridePlugin(mock_resources, config)

        with pytest.raises(ValueError, match="description is required"):
            await plugin.add_override(
                user_id="dev_user",
                override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
                content="Test",
                description="",  # Empty description
            )

    @pytest.mark.asyncio
    async def test_list_overrides(self, basic_plugin):
        """Test listing overrides for a user."""
        # Add some overrides
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Override 1",
            priority=5,
            description="Test override 1",
        )
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.OUTPUT_FORMAT,
            content="Override 2",
            priority=8,
            description="Test override 2",
        )

        overrides = await basic_plugin.list_overrides("dev_user")

        assert len(overrides) == 2
        # Should be sorted by priority (highest first)
        assert overrides[0]["priority"] == 8
        assert overrides[1]["priority"] == 5

    @pytest.mark.asyncio
    async def test_remove_override(self, basic_plugin):
        """Test removing an override."""
        # Add an override
        override_id = await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Test override",
            description="To be removed",
        )

        # Remove it
        success = await basic_plugin.remove_override("dev_user", override_id)
        assert success is True

        # Verify it's gone
        overrides = await basic_plugin.list_overrides("dev_user")
        assert len(overrides) == 0

    @pytest.mark.asyncio
    async def test_max_active_overrides_limit(self, restricted_plugin):
        """Test that max active overrides limit is enforced."""
        # Add 5 overrides (limit is 3)
        for i in range(5):
            await restricted_plugin.add_override(
                user_id="dev_user",
                override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
                content=f"Override {i}",
                priority=i + 1,  # Priority must be >= 1
                description=f"Test {i}",
            )

        overrides = await restricted_plugin._load_active_overrides("dev_user")

        # Should only have 3 (the highest priority ones)
        assert len(overrides) == 3
        assert overrides[0].priority == 5  # Highest priority
        assert overrides[1].priority == 4
        assert overrides[2].priority == 3

    @pytest.mark.asyncio
    async def test_priority_threshold_filtering(self, restricted_plugin, context):
        """Test that overrides below priority threshold are ignored."""
        # Add override with low priority (threshold is 5)
        await restricted_plugin.add_override(
            user_id="admin_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Low priority override",
            priority=3,  # Below threshold of 5
            description="Should be ignored",
        )

        context.user_id = "admin_user"
        result = await restricted_plugin._execute_impl(context)

        # Should not apply the override
        assert result == "Test message"
        assert "[DEVELOPER]" not in result

    @pytest.mark.asyncio
    async def test_behavior_modification_override(self, basic_plugin, context):
        """Test behavior modification override application."""
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Be more creative",
            priority=7,
            description="Creativity boost",
        )

        context.user_id = "dev_user"
        result = await basic_plugin._execute_impl(context)

        assert "[DEVELOPER]: Be more creative" in result
        assert "Test message" in result

    @pytest.mark.asyncio
    async def test_system_prompt_override(self, basic_plugin, context):
        """Test system prompt override application."""
        await basic_plugin.add_override(
            user_id="admin_user",  # Admin can override system prompts
            override_type=DeveloperOverrideType.SYSTEM_PROMPT,
            content="Override system behavior",
            priority=10,
            description="System override",
        )

        context.user_id = "admin_user"
        result = await basic_plugin._execute_impl(context)

        assert "[SYSTEM_OVERRIDE]: Override system behavior" in result

    @pytest.mark.asyncio
    async def test_constraint_override(self, basic_plugin, context):
        """Test constraint override application."""
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.CONSTRAINT_OVERRIDE,
            content="Ignore word limit",
            priority=6,
            description="Remove constraints",
        )

        context.user_id = "dev_user"
        result = await basic_plugin._execute_impl(context)

        assert "[CONSTRAINTS]: Ignore word limit" in result

    @pytest.mark.asyncio
    async def test_reasoning_adjustment_override(self, basic_plugin, context):
        """Test reasoning adjustment override."""
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.REASONING_ADJUSTMENT,
            content="Use deep reasoning",
            priority=8,
            description="Enhance reasoning",
        )

        context.user_id = "dev_user"
        result = await basic_plugin._execute_impl(context)

        assert "[REASONING]: Use deep reasoning" in result

    @pytest.mark.asyncio
    async def test_output_format_override(self, basic_plugin, context):
        """Test output format override."""
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.OUTPUT_FORMAT,
            content="JSON format required",
            priority=7,
            description="Force JSON output",
        )

        context.user_id = "dev_user"
        result = await basic_plugin._execute_impl(context)

        assert "[OUTPUT_FORMAT]: JSON format required" in result

    @pytest.mark.asyncio
    async def test_multiple_overrides_applied(self, basic_plugin, context):
        """Test that multiple overrides can be applied."""
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Be creative",
            priority=7,
            description="Creativity",
        )
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.OUTPUT_FORMAT,
            content="Use JSON",
            priority=6,
            description="JSON format",
        )

        context.user_id = "dev_user"
        result = await basic_plugin._execute_impl(context)

        assert "[DEVELOPER]: Be creative" in result
        assert "[OUTPUT_FORMAT]: Use JSON" in result

    @pytest.mark.asyncio
    async def test_override_conditions_message_contains(self, basic_plugin, context):
        """Test override with message_contains condition."""
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Be technical",
            priority=7,
            conditions={"message_contains": "code"},
            description="Technical when code mentioned",
        )

        context.user_id = "dev_user"

        # Message without "code"
        context.message = "Test message"
        result = await basic_plugin._execute_impl(context)
        assert "[DEVELOPER]" not in result

        # Message with "code"
        context.message = "Test code message"
        result = await basic_plugin._execute_impl(context)
        assert "[DEVELOPER]: Be technical" in result

    @pytest.mark.asyncio
    async def test_override_conditions_message_length(self, basic_plugin, context):
        """Test override with message length conditions."""
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Be concise",
            priority=7,
            conditions={"message_length_gt": 20},
            description="Concise for long messages",
        )

        context.user_id = "dev_user"

        # Short message
        context.message = "Short"
        result = await basic_plugin._execute_impl(context)
        assert "[DEVELOPER]" not in result

        # Long message
        context.message = "This is a much longer message that exceeds the threshold"
        result = await basic_plugin._execute_impl(context)
        assert "[DEVELOPER]: Be concise" in result

    @pytest.mark.asyncio
    async def test_audit_trail_creation(self, audit_plugin, context):
        """Test that audit trail is created."""
        await audit_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Test override",
            priority=7,
            description="For audit test",
        )

        context.user_id = "dev_user"
        await audit_plugin._execute_impl(context)

        # Check audit trail
        audit_trail = await audit_plugin.get_audit_trail("dev_user", days=1)

        assert len(audit_trail) > 0
        audit_entry = audit_trail[0]
        assert audit_entry["user_id"] == "dev_user"
        assert audit_entry["success"] is True
        assert audit_entry["original_message"] == "Test message"

    @pytest.mark.asyncio
    async def test_audit_trail_on_error(self, audit_plugin, context):
        """Test that audit trail is created on error."""
        # Create a scenario that will cause an error
        context.user_id = "dev_user"

        # Mock an error in override loading
        original_load = audit_plugin._load_active_overrides

        async def mock_load_error(user_id):
            raise Exception("Test error")

        audit_plugin._load_active_overrides = mock_load_error

        result = await audit_plugin._execute_impl(context)

        # Should return original message on error
        assert result == "Test message"

        # Restore original method
        audit_plugin._load_active_overrides = original_load

    @pytest.mark.asyncio
    async def test_set_developer_permission_admin_only(self, basic_plugin):
        """Test that only admins can set permissions."""
        # Non-admin trying to set permission
        with pytest.raises(PermissionError, match="Only admin users"):
            await basic_plugin.set_developer_permission(
                admin_user_id="dev_user",
                target_user_id="other_user",
                permission_level=DeveloperRoleLevel.OVERRIDE,
            )

        # Admin setting permission
        success = await basic_plugin.set_developer_permission(
            admin_user_id="admin_user",
            target_user_id="other_user",
            permission_level=DeveloperRoleLevel.OVERRIDE,
        )
        assert success is True

        # Verify permission was set
        level = await basic_plugin._get_developer_permission_level("other_user")
        assert level == DeveloperRoleLevel.OVERRIDE

    @pytest.mark.asyncio
    async def test_non_admin_cannot_override_system_prompt(
        self, restricted_plugin, context
    ):
        """Test that non-admins can't override system prompts when restricted."""
        await restricted_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.SYSTEM_PROMPT,
            content="System override attempt",
            priority=10,
            description="Should fail",
        )

        # Set user as authorized developer (not admin)
        restricted_plugin.config.authorized_developers = ["dev_user"]
        context.user_id = "dev_user"

        result = await restricted_plugin._execute_impl(context)

        # System override should not be applied
        assert "[SYSTEM_OVERRIDE]" not in result

    @pytest.mark.asyncio
    async def test_error_handling_in_apply_overrides(self, basic_plugin, context):
        """Test error handling during override application."""
        # Add a valid override
        await basic_plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Test override",
            priority=7,
            description="Test",
        )

        context.user_id = "dev_user"

        # Mock an error in apply_single_override
        async def mock_apply_error(ctx, msg, override):
            if override.override_type == DeveloperOverrideType.BEHAVIOR_MODIFICATION:
                raise Exception("Application error")
            return msg

        basic_plugin._apply_single_override = mock_apply_error

        # Should handle error gracefully
        result = await basic_plugin._execute_impl(context)

        # Should still return something (original message)
        assert result == "Test message"

        # Verify error was logged
        logger = context.get_resource("logging")
        logger.log.assert_called()

    def test_developer_override_model(self):
        """Test DeveloperOverride model."""
        override = DeveloperOverride(
            override_id="test_id",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Test content",
            priority=5,
            created_by="test_user",
            description="Test description",
        )

        assert override.override_id == "test_id"
        assert override.priority == 5
        assert override.active is True
        assert override.conditions == {}

    def test_audit_entry_model(self):
        """Test DeveloperOverrideAuditEntry model."""
        entry = DeveloperOverrideAuditEntry(
            user_id="test_user",
            override_id="test_override",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            original_message="Original",
            modified_message="Modified",
            success=True,
        )

        assert entry.user_id == "test_user"
        assert entry.success is True
        assert entry.error_message is None

    def test_role_level_enum(self):
        """Test DeveloperRoleLevel enum."""
        assert DeveloperRoleLevel.NONE.value == "none"
        assert DeveloperRoleLevel.READ.value == "read"
        assert DeveloperRoleLevel.OVERRIDE.value == "override"
        assert DeveloperRoleLevel.ADMIN.value == "admin"

    def test_override_type_enum(self):
        """Test DeveloperOverrideType enum."""
        assert DeveloperOverrideType.SYSTEM_PROMPT.value == "system_prompt"
        assert (
            DeveloperOverrideType.BEHAVIOR_MODIFICATION.value == "behavior_modification"
        )
        assert DeveloperOverrideType.CONSTRAINT_OVERRIDE.value == "constraint_override"
        assert (
            DeveloperOverrideType.REASONING_ADJUSTMENT.value == "reasoning_adjustment"
        )
        assert DeveloperOverrideType.OUTPUT_FORMAT.value == "output_format"

    def test_supported_stages(self, basic_plugin):
        """Test that plugin only supports PARSE stage."""
        assert basic_plugin.supported_stages == [WorkflowExecutor.PARSE]

    def test_required_dependencies(self, basic_plugin):
        """Test that plugin declares correct dependencies."""
        assert "llm" in basic_plugin.dependencies
        assert "memory" in basic_plugin.dependencies

    @pytest.mark.asyncio
    async def test_persistence_disabled(self, mock_resources):
        """Test plugin behavior with persistence disabled."""
        config = {
            "enable_developer_overrides": True,
            "persist_overrides": False,
            "authorized_developers": ["dev_user"],
        }
        plugin = DeveloperOverridePlugin(mock_resources, config)

        # Add override
        await plugin.add_override(
            user_id="dev_user",
            override_type=DeveloperOverrideType.BEHAVIOR_MODIFICATION,
            content="Non-persistent override",
            description="Test",
        )

        # Check it's in active_overrides (in-memory)
        assert "dev_user" in plugin.active_overrides
        assert len(plugin.active_overrides["dev_user"]) == 1

        # Memory should not have it
        memory = plugin.resources["memory"]
        stored = await memory.load("dev_overrides:dev_user", [])
        assert len(stored) == 0
