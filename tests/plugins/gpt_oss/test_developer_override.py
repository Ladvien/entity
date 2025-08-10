"""Tests for Developer Override Plugin."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entity.plugins.context import PluginContext
from entity.plugins.gpt_oss.developer_override import (
    AuditEntry,
    DeveloperOverride,
    DeveloperOverridePlugin,
    OverrideScope,
    PermissionLevel,
)
from entity.workflow.executor import WorkflowExecutor


@pytest.fixture
def mock_resources():
    """Create mock resources for testing."""
    resources = MagicMock()
    memory_resource = AsyncMock()
    memory_resource.store = AsyncMock()
    memory_resource.load = AsyncMock(return_value=None)
    resources.get.return_value = memory_resource
    return resources


@pytest.fixture
def mock_context():
    """Create mock plugin context for testing."""
    context = MagicMock(spec=PluginContext)
    context.user_id = "test_user"
    context.message = "Hello, please help me with this task."
    context.resources = MagicMock()
    return context


@pytest.fixture
def plugin_config():
    """Create plugin configuration for testing."""
    return DeveloperOverridePlugin.ConfigModel(
        enabled=True,
        developer_permissions={
            "admin_dev": PermissionLevel.FULL_ADMIN,
            "regular_dev": PermissionLevel.MODIFY,
            "readonly_dev": PermissionLevel.READ_ONLY,
        },
        enable_audit_trail=True,
        max_active_overrides=5,
    )


@pytest.fixture
def test_override():
    """Create test override for testing."""
    return DeveloperOverride(
        id="test_override_1",
        instructions="Please be more helpful and detailed in your responses.",
        scope=OverrideScope.USER,
        user_id="test_user",
        created_by="admin_dev",
        created_at=datetime.now(),
        priority=1,
        active=True,
    )


class TestDeveloperOverride:
    """Test cases for DeveloperOverride dataclass."""

    def test_override_creation(self):
        """Test creating a developer override."""
        now = datetime.now()
        override = DeveloperOverride(
            id="test_1",
            instructions="Test instructions",
            scope=OverrideScope.SESSION,
            created_by="dev1",
            created_at=now,
            priority=5,
        )

        assert override.id == "test_1"
        assert override.instructions == "Test instructions"
        assert override.scope == OverrideScope.SESSION
        assert override.created_by == "dev1"
        assert override.created_at == now
        assert override.priority == 5
        assert override.active is True

    def test_matches_context_user_scope(self, mock_context):
        """Test override matching for user scope."""
        override = DeveloperOverride(
            id="test_1",
            instructions="Test",
            scope=OverrideScope.USER,
            user_id="test_user",
            active=True,
        )

        assert override.matches_context(mock_context) is True

        # Different user should not match
        mock_context.user_id = "different_user"
        assert override.matches_context(mock_context) is False

    def test_matches_context_global_scope(self, mock_context):
        """Test override matching for global scope."""
        override = DeveloperOverride(
            id="test_1",
            instructions="Test",
            scope=OverrideScope.GLOBAL,
            active=True,
        )

        assert override.matches_context(mock_context) is True

    def test_matches_context_inactive(self, mock_context):
        """Test that inactive overrides don't match."""
        override = DeveloperOverride(
            id="test_1",
            instructions="Test",
            scope=OverrideScope.GLOBAL,
            active=False,
        )

        assert override.matches_context(mock_context) is False

    def test_matches_context_expired(self, mock_context):
        """Test that expired overrides don't match."""
        past_time = datetime.now() - timedelta(hours=1)
        override = DeveloperOverride(
            id="test_1",
            instructions="Test",
            scope=OverrideScope.GLOBAL,
            expires_at=past_time,
            active=True,
        )

        assert override.matches_context(mock_context) is False

    def test_matches_context_conditional(self, mock_context):
        """Test conditional override matching."""
        override = DeveloperOverride(
            id="test_1",
            instructions="Test",
            scope=OverrideScope.CONDITIONAL,
            conditions={"user_id": "test_user"},
            active=True,
        )

        assert override.matches_context(mock_context) is True

        # Different condition value should not match
        override.conditions = {"user_id": "different_user"}
        assert override.matches_context(mock_context) is False


class TestDeveloperOverridePlugin:
    """Test cases for DeveloperOverridePlugin."""

    def test_plugin_initialization(self, mock_resources, plugin_config):
        """Test plugin initialization."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        assert plugin.supported_stages == [WorkflowExecutor.PARSE]
        assert plugin.config.enabled is True
        assert len(plugin.config.developer_permissions) == 3
        assert plugin._active_overrides == {}
        assert plugin._audit_trail == []

    @pytest.mark.asyncio
    async def test_plugin_disabled(self, mock_resources, plugin_config, mock_context):
        """Test plugin behavior when disabled."""
        plugin_config.enabled = False
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        result = await plugin._execute_impl(mock_context)
        assert result == mock_context.message

    @pytest.mark.asyncio
    async def test_execute_no_overrides(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test execution with no applicable overrides."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        result = await plugin._execute_impl(mock_context)

        assert result == mock_context.message

    @pytest.mark.asyncio
    async def test_execute_with_override(
        self, mock_resources, plugin_config, mock_context, test_override
    ):
        """Test execution with applicable override."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)
        plugin._active_overrides[test_override.id] = test_override

        result = await plugin._execute_impl(mock_context)

        assert "[DEVELOPER OVERRIDE - ID: test_override_1]" in result
        assert test_override.instructions in result
        assert mock_context.message in result

    @pytest.mark.asyncio
    async def test_execute_multiple_overrides_priority(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test execution with multiple overrides respects priority."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Create two overrides with different priorities
        override1 = DeveloperOverride(
            id="override_1",
            instructions="Low priority instruction",
            scope=OverrideScope.GLOBAL,
            created_by="admin_dev",
            priority=1,
            active=True,
        )

        override2 = DeveloperOverride(
            id="override_2",
            instructions="High priority instruction",
            scope=OverrideScope.GLOBAL,
            created_by="admin_dev",
            priority=10,
            active=True,
        )

        plugin._active_overrides["override_1"] = override1
        plugin._active_overrides["override_2"] = override2

        result = await plugin._execute_impl(mock_context)

        # Higher priority should appear first
        assert result.find("High priority instruction") < result.find(
            "Low priority instruction"
        )

    def test_get_permission_level(self, mock_resources, plugin_config):
        """Test permission level retrieval."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        assert plugin._get_permission_level("admin_dev") == PermissionLevel.FULL_ADMIN
        assert plugin._get_permission_level("regular_dev") == PermissionLevel.MODIFY
        assert plugin._get_permission_level("readonly_dev") == PermissionLevel.READ_ONLY
        assert (
            plugin._get_permission_level("unknown_dev")
            == plugin_config.default_permission_level
        )

    @pytest.mark.asyncio
    async def test_has_permission_for_override(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test permission checking for overrides."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Admin can apply any override
        admin_override = DeveloperOverride(
            id="test_1",
            instructions="Test",
            scope=OverrideScope.USER,
            created_by="admin_dev",
            active=True,
        )
        assert (
            await plugin._has_permission_for_override(admin_override, mock_context)
            is True
        )

        # Regular dev can apply non-global overrides
        regular_override = DeveloperOverride(
            id="test_2",
            instructions="Test",
            scope=OverrideScope.USER,
            created_by="regular_dev",
            active=True,
        )
        assert (
            await plugin._has_permission_for_override(regular_override, mock_context)
            is True
        )

        # Read-only dev cannot apply overrides
        readonly_override = DeveloperOverride(
            id="test_3",
            instructions="Test",
            scope=OverrideScope.USER,
            created_by="readonly_dev",
            active=True,
        )
        assert (
            await plugin._has_permission_for_override(readonly_override, mock_context)
            is False
        )

    @pytest.mark.asyncio
    async def test_has_permission_global_override(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test permission checking for global overrides."""
        plugin_config.allow_global_overrides = True
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Only admin can apply global overrides
        global_override = DeveloperOverride(
            id="test_1",
            instructions="Test",
            scope=OverrideScope.GLOBAL,
            created_by="admin_dev",
            active=True,
        )
        assert (
            await plugin._has_permission_for_override(global_override, mock_context)
            is True
        )

        # Regular dev cannot apply global overrides
        global_override.created_by = "regular_dev"
        assert (
            await plugin._has_permission_for_override(global_override, mock_context)
            is False
        )

    @pytest.mark.asyncio
    async def test_create_override_success(self, mock_resources, plugin_config):
        """Test successful override creation."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        override_id = await plugin.create_override(
            instructions="Test instructions",
            scope=OverrideScope.USER,
            developer_id="admin_dev",
            user_id="test_user",
            priority=5,
        )

        assert override_id is not None
        assert override_id in plugin._active_overrides

        override = plugin._active_overrides[override_id]
        assert override.instructions == "Test instructions"
        assert override.scope == OverrideScope.USER
        assert override.user_id == "test_user"
        assert override.created_by == "admin_dev"
        assert override.priority == 5
        assert override.active is True

    @pytest.mark.asyncio
    async def test_create_override_no_permission(self, mock_resources, plugin_config):
        """Test override creation with insufficient permissions."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        with pytest.raises(ValueError, match="no override permissions"):
            await plugin.create_override(
                instructions="Test instructions",
                scope=OverrideScope.USER,
                developer_id="unknown_dev",
            )

    @pytest.mark.asyncio
    async def test_create_override_readonly_permission(
        self, mock_resources, plugin_config
    ):
        """Test override creation with read-only permissions."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        with pytest.raises(ValueError, match="read-only permissions"):
            await plugin.create_override(
                instructions="Test instructions",
                scope=OverrideScope.USER,
                developer_id="readonly_dev",
            )

    @pytest.mark.asyncio
    async def test_create_override_global_without_admin(
        self, mock_resources, plugin_config
    ):
        """Test global override creation without admin permissions."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        with pytest.raises(ValueError, match="Global overrides require full admin"):
            await plugin.create_override(
                instructions="Test instructions",
                scope=OverrideScope.GLOBAL,
                developer_id="regular_dev",
            )

    @pytest.mark.asyncio
    async def test_create_override_too_long(self, mock_resources, plugin_config):
        """Test override creation with instructions too long."""
        plugin_config.max_instruction_length = 100
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        long_instructions = "x" * 150

        with pytest.raises(ValueError, match="Instructions too long"):
            await plugin.create_override(
                instructions=long_instructions,
                scope=OverrideScope.USER,
                developer_id="admin_dev",
            )

    @pytest.mark.asyncio
    async def test_create_override_max_reached(self, mock_resources, plugin_config):
        """Test override creation when max overrides reached."""
        plugin_config.max_active_overrides = 1
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Create first override
        await plugin.create_override(
            instructions="First override",
            scope=OverrideScope.USER,
            developer_id="admin_dev",
        )

        # Second should fail
        with pytest.raises(ValueError, match="Maximum active overrides reached"):
            await plugin.create_override(
                instructions="Second override",
                scope=OverrideScope.USER,
                developer_id="admin_dev",
            )

    @pytest.mark.asyncio
    async def test_disable_override_success(self, mock_resources, plugin_config):
        """Test successful override disabling."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Create override
        override_id = await plugin.create_override(
            instructions="Test instructions",
            scope=OverrideScope.USER,
            developer_id="admin_dev",
        )

        # Disable it
        result = await plugin.disable_override(override_id, "admin_dev")

        assert result is True
        assert plugin._active_overrides[override_id].active is False

    @pytest.mark.asyncio
    async def test_disable_override_not_found(self, mock_resources, plugin_config):
        """Test disabling non-existent override."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        result = await plugin.disable_override("nonexistent", "admin_dev")

        assert result is False

    @pytest.mark.asyncio
    async def test_disable_override_insufficient_permission(
        self, mock_resources, plugin_config
    ):
        """Test disabling override with insufficient permissions."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Create override by admin
        override_id = await plugin.create_override(
            instructions="Test instructions",
            scope=OverrideScope.USER,
            developer_id="admin_dev",
        )

        # Try to disable by regular dev
        with pytest.raises(ValueError, match="Insufficient permissions"):
            await plugin.disable_override(override_id, "regular_dev")

    @pytest.mark.asyncio
    async def test_list_overrides_admin(self, mock_resources, plugin_config):
        """Test listing overrides as admin."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Create multiple overrides
        await plugin.create_override(
            instructions="Admin override",
            scope=OverrideScope.USER,
            developer_id="admin_dev",
        )

        await plugin.create_override(
            instructions="Regular override",
            scope=OverrideScope.USER,
            developer_id="regular_dev",
        )

        # Admin should see all overrides
        overrides = await plugin.list_overrides("admin_dev")

        assert len(overrides) == 2
        assert any("Admin override" in o["instructions"] for o in overrides)
        assert any("Regular override" in o["instructions"] for o in overrides)

    @pytest.mark.asyncio
    async def test_list_overrides_regular_dev(self, mock_resources, plugin_config):
        """Test listing overrides as regular developer."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Create overrides by different developers
        await plugin.create_override(
            instructions="Admin override",
            scope=OverrideScope.USER,
            developer_id="admin_dev",
        )

        await plugin.create_override(
            instructions="Regular override",
            scope=OverrideScope.USER,
            developer_id="regular_dev",
        )

        # Regular dev should only see their own overrides
        overrides = await plugin.list_overrides("regular_dev")

        assert len(overrides) == 1
        assert "Regular override" in overrides[0]["instructions"]

    @pytest.mark.asyncio
    async def test_list_overrides_no_permission(self, mock_resources, plugin_config):
        """Test listing overrides with no permissions."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        await plugin.create_override(
            instructions="Test override",
            scope=OverrideScope.USER,
            developer_id="admin_dev",
        )

        # Unknown dev should see no overrides
        overrides = await plugin.list_overrides("unknown_dev")

        assert len(overrides) == 0

    @pytest.mark.asyncio
    async def test_audit_trail_creation(self, mock_resources, plugin_config):
        """Test audit trail entry creation."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        await plugin._log_audit_entry(
            action="created",
            override_id="test_1",
            user_id="test_user",
            developer_id="admin_dev",
            instructions="Test instructions",
            context={"priority": 1},
        )

        assert len(plugin._audit_trail) == 1

        entry = plugin._audit_trail[0]
        assert entry.action == "created"
        assert entry.override_id == "test_1"
        assert entry.user_id == "test_user"
        assert entry.developer_id == "admin_dev"
        assert entry.instructions == "Test instructions"
        assert entry.context == {"priority": 1}

    def test_get_audit_trail_admin(self, mock_resources, plugin_config):
        """Test getting audit trail as admin."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Add some audit entries
        plugin._audit_trail = [
            AuditEntry(
                timestamp=datetime.now(),
                override_id="test_1",
                user_id="user_1",
                developer_id="admin_dev",
                action="created",
                instructions="Test 1",
                context={},
                result="success",
            ),
            AuditEntry(
                timestamp=datetime.now(),
                override_id="test_2",
                user_id="user_2",
                developer_id="regular_dev",
                action="created",
                instructions="Test 2",
                context={},
                result="success",
            ),
        ]

        # Admin should see all entries
        entries = plugin.get_audit_trail("admin_dev")

        assert len(entries) == 2

    def test_get_audit_trail_regular_dev(self, mock_resources, plugin_config):
        """Test getting audit trail as regular developer."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Add some audit entries
        plugin._audit_trail = [
            AuditEntry(
                timestamp=datetime.now(),
                override_id="test_1",
                user_id="user_1",
                developer_id="admin_dev",
                action="created",
                instructions="Test 1",
                context={},
                result="success",
            ),
            AuditEntry(
                timestamp=datetime.now(),
                override_id="test_2",
                user_id="user_2",
                developer_id="regular_dev",
                action="created",
                instructions="Test 2",
                context={},
                result="success",
            ),
        ]

        # Regular dev should only see their own entries
        entries = plugin.get_audit_trail("regular_dev")

        assert len(entries) == 1
        assert entries[0]["developer_id"] == "regular_dev"

    def test_get_audit_trail_no_permission(self, mock_resources, plugin_config):
        """Test getting audit trail with no permissions."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        plugin._audit_trail = [
            AuditEntry(
                timestamp=datetime.now(),
                override_id="test_1",
                user_id="user_1",
                developer_id="admin_dev",
                action="created",
                instructions="Test 1",
                context={},
                result="success",
            )
        ]

        # Unknown dev should see no entries
        entries = plugin.get_audit_trail("unknown_dev")

        assert len(entries) == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_overrides(self, mock_resources, plugin_config):
        """Test cleanup of expired overrides."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Create expired override
        past_time = datetime.now() - timedelta(hours=1)
        expired_override = DeveloperOverride(
            id="expired_1",
            instructions="Expired override",
            scope=OverrideScope.USER,
            expires_at=past_time,
            active=True,
        )

        # Create active override
        future_time = datetime.now() + timedelta(hours=1)
        active_override = DeveloperOverride(
            id="active_1",
            instructions="Active override",
            scope=OverrideScope.USER,
            expires_at=future_time,
            active=True,
        )

        plugin._active_overrides["expired_1"] = expired_override
        plugin._active_overrides["active_1"] = active_override

        # Cleanup
        cleaned_count = await plugin.cleanup_expired_overrides()

        assert cleaned_count == 1
        assert plugin._active_overrides["expired_1"].active is False
        assert plugin._active_overrides["active_1"].active is True

    @pytest.mark.asyncio
    async def test_save_overrides_to_memory(self, mock_resources, plugin_config):
        """Test saving overrides to memory."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Add an override
        override = DeveloperOverride(
            id="test_1",
            instructions="Test instructions",
            scope=OverrideScope.USER,
            user_id="test_user",
            created_by="admin_dev",
            created_at=datetime.now(),
            priority=1,
            active=True,
        )
        plugin._active_overrides["test_1"] = override

        await plugin._save_overrides_to_memory()

        # Verify memory.store was called
        mock_resources.get.return_value.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_error_handling(
        self, mock_resources, plugin_config, mock_context
    ):
        """Test execution with error handling."""
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        # Mock an error in _get_applicable_overrides
        with patch.object(
            plugin, "_get_applicable_overrides", side_effect=Exception("Test error")
        ):
            result = await plugin._execute_impl(mock_context)

            # Should return original message on error
            assert result == mock_context.message

    @pytest.mark.asyncio
    async def test_create_override_with_expiration(self, mock_resources, plugin_config):
        """Test creating override with expiration."""
        plugin_config.allow_permanent_overrides = True
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        future_time = datetime.now() + timedelta(hours=1)

        override_id = await plugin.create_override(
            instructions="Test instructions",
            scope=OverrideScope.USER,
            developer_id="admin_dev",
            expires_at=future_time,
        )

        override = plugin._active_overrides[override_id]
        assert override.expires_at == future_time

    @pytest.mark.asyncio
    async def test_create_override_default_expiration(
        self, mock_resources, plugin_config
    ):
        """Test creating override with default expiration when permanent not allowed."""
        plugin_config.allow_permanent_overrides = False
        plugin = DeveloperOverridePlugin(mock_resources, plugin_config)

        override_id = await plugin.create_override(
            instructions="Test instructions",
            scope=OverrideScope.USER,
            developer_id="admin_dev",
        )

        override = plugin._active_overrides[override_id]
        assert override.expires_at is not None
        assert override.expires_at > datetime.now()


class TestPermissionLevel:
    """Test cases for PermissionLevel enum."""

    def test_permission_levels(self):
        """Test permission level enum values."""
        assert PermissionLevel.NONE.value == "none"
        assert PermissionLevel.READ_ONLY.value == "read_only"
        assert PermissionLevel.MODIFY.value == "modify"
        assert PermissionLevel.FULL_ADMIN.value == "full_admin"


class TestOverrideScope:
    """Test cases for OverrideScope enum."""

    def test_override_scopes(self):
        """Test override scope enum values."""
        assert OverrideScope.SESSION.value == "session"
        assert OverrideScope.USER.value == "user"
        assert OverrideScope.GLOBAL.value == "global"
        assert OverrideScope.CONDITIONAL.value == "conditional"


class TestConfigModel:
    """Test cases for DeveloperOverridePlugin.ConfigModel."""

    def test_config_model_defaults(self):
        """Test ConfigModel default values."""
        config = DeveloperOverridePlugin.ConfigModel()

        assert config.enabled is True
        assert config.require_explicit_permission is True
        assert config.default_permission_level == PermissionLevel.NONE
        assert config.developer_permissions == {}
        assert config.max_active_overrides == 10
        assert config.default_override_priority == 0
        assert config.allow_global_overrides is False
        assert config.allow_permanent_overrides is False
        assert config.enable_audit_trail is True
        assert config.log_all_override_attempts is True
        assert config.require_justification is False
        assert config.max_instruction_length == 5000
        assert config.memory_key_prefix == "developer_override"
        assert config.audit_retention_days == 90

    def test_config_model_custom_values(self):
        """Test ConfigModel with custom values."""
        config = DeveloperOverridePlugin.ConfigModel(
            enabled=False,
            max_active_overrides=20,
            allow_global_overrides=True,
            developer_permissions={"dev1": PermissionLevel.FULL_ADMIN},
            max_instruction_length=1000,
        )

        assert config.enabled is False
        assert config.max_active_overrides == 20
        assert config.allow_global_overrides is True
        assert config.developer_permissions == {"dev1": PermissionLevel.FULL_ADMIN}
        assert config.max_instruction_length == 1000


if __name__ == "__main__":
    pytest.main([__file__])
