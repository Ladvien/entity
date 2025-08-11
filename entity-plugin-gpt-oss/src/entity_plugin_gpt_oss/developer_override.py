"""Developer Override Plugin for Entity Framework GPT-OSS Integration.

This plugin leverages harmony's developer role to inject behavior modifications
that safely override system prompts when needed. It maintains proper role hierarchy
and provides comprehensive audit trails for all developer interventions.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext
from entity.workflow.executor import WorkflowExecutor
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Developer permission levels."""

    NONE = "none"
    READ_ONLY = "read_only"
    MODIFY = "modify"
    FULL_ADMIN = "full_admin"


class OverrideScope(Enum):
    """Scope of developer override."""

    SESSION = "session"  # Override for current session only
    USER = "user"  # Override for specific user
    GLOBAL = "global"  # Override for all interactions
    CONDITIONAL = "conditional"  # Override with conditions


@dataclass
class DeveloperOverride:
    """Represents a developer override instruction."""

    id: str
    instructions: str
    scope: OverrideScope
    user_id: str | None = None
    conditions: dict[str, Any] | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
    priority: int = 0  # Higher numbers have higher priority
    active: bool = True

    def matches_context(self, context: PluginContext) -> bool:
        """Check if this override applies to the given context."""
        if not self.active:
            return False

        if self.expires_at and datetime.now() > self.expires_at:
            return False

        if self.scope == OverrideScope.USER and self.user_id != context.user_id:
            return False

        if self.scope == OverrideScope.CONDITIONAL and self.conditions:
            return self._evaluate_conditions(context)

        return True

    def _evaluate_conditions(self, context: PluginContext) -> bool:
        """Evaluate conditional logic for override application."""
        if not self.conditions:
            return False

        # Simple condition evaluation (can be extended)
        for condition_key, condition_value in self.conditions.items():
            context_value = getattr(context, condition_key, None)
            if context_value != condition_value:
                return False

        return True


@dataclass
class AuditEntry:
    """Audit trail entry for developer override usage."""

    timestamp: datetime
    override_id: str
    user_id: str
    developer_id: str
    action: str  # "applied", "created", "modified", "disabled"
    instructions: str
    context: dict[str, Any]
    result: str


class DeveloperOverridePlugin(Plugin):
    """Plugin that enables developer role overrides with proper permissions and auditing.

    This plugin runs in the PARSE stage to inject developer instructions that can
    override system behavior. It maintains role hierarchy (developer > user) and
    provides comprehensive audit trails for all overrides.
    """

    supported_stages = [WorkflowExecutor.PARSE]

    class ConfigModel(BaseModel):
        """Configuration for developer override plugin."""

        # Permission system
        enabled: bool = True
        require_explicit_permission: bool = True
        default_permission_level: PermissionLevel = PermissionLevel.NONE
        developer_permissions: dict[str, PermissionLevel] = Field(default_factory=dict)

        # Override behavior
        max_active_overrides: int = 10
        default_override_priority: int = 0
        allow_global_overrides: bool = False
        allow_permanent_overrides: bool = False

        # Audit and security
        enable_audit_trail: bool = True
        log_all_override_attempts: bool = True
        require_justification: bool = False
        max_instruction_length: int = 5000

        # Integration settings
        memory_key_prefix: str = "developer_override"
        audit_retention_days: int = 90

        class Config:
            use_enum_values = True

    def __init__(self, resources, config=None):
        """Initialize the developer override plugin.

        Args:
            resources: Entity framework resources
            config: Plugin configuration
        """
        super().__init__(resources, config)
        self._active_overrides: dict[str, DeveloperOverride] = {}
        self._audit_trail: list[AuditEntry] = []

        # Load existing overrides from memory
        self._load_overrides_from_memory()

    async def _execute_impl(self, context: PluginContext) -> str:
        """Execute developer override logic.

        Args:
            context: Plugin execution context

        Returns:
            Original message potentially modified with developer instructions
        """
        if not self.config.enabled:
            return context.message

        logger.debug("Checking for developer overrides")

        try:
            # Get applicable overrides
            applicable_overrides = await self._get_applicable_overrides(context)

            if not applicable_overrides:
                return context.message

            # Sort by priority (highest first)
            applicable_overrides.sort(key=lambda x: x.priority, reverse=True)

            # Apply overrides
            modified_message = context.message
            for override in applicable_overrides:
                modified_message = await self._apply_override(
                    override, modified_message, context
                )

            return modified_message

        except Exception as e:
            logger.error(f"Error in developer override execution: {e}")
            if self.config.log_all_override_attempts:
                await self._log_audit_entry(
                    "error",
                    "",
                    context.user_id,
                    "system",
                    str(e),
                    {"original_message": context.message},
                )
            return context.message

    async def _get_applicable_overrides(
        self, context: PluginContext
    ) -> list[DeveloperOverride]:
        """Get all overrides that apply to the current context.

        Args:
            context: Plugin execution context

        Returns:
            List of applicable overrides
        """
        applicable = []

        for override in self._active_overrides.values():
            if override.matches_context(context):
                # Check if developer has permission to apply this override
                if await self._has_permission_for_override(override, context):
                    applicable.append(override)

        return applicable

    async def _apply_override(
        self, override: DeveloperOverride, message: str, context: PluginContext
    ) -> str:
        """Apply a developer override to the message.

        Args:
            override: Override to apply
            message: Current message
            context: Plugin execution context

        Returns:
            Modified message with developer instructions
        """
        # Create developer instruction prefix
        developer_instruction = f"""[DEVELOPER OVERRIDE - ID: {override.id}]
{override.instructions}

[END DEVELOPER OVERRIDE]

{message}"""

        # Log the override application
        if self.config.enable_audit_trail:
            await self._log_audit_entry(
                "applied",
                override.id,
                context.user_id,
                override.created_by or "unknown",
                override.instructions,
                {
                    "scope": override.scope.value,
                    "priority": override.priority,
                    "original_message_length": len(message),
                },
            )

        logger.info(
            f"Applied developer override {override.id} for user {context.user_id}"
        )

        return developer_instruction

    async def _has_permission_for_override(
        self, override: DeveloperOverride, context: PluginContext
    ) -> bool:
        """Check if the current context has permission for the override.

        Args:
            override: Override to check
            context: Plugin execution context

        Returns:
            True if permission is granted
        """
        # Get developer permission level
        developer_id = override.created_by or "unknown"
        permission_level = self._get_permission_level(developer_id)

        if permission_level == PermissionLevel.NONE:
            return False

        if permission_level == PermissionLevel.READ_ONLY:
            return False  # Read-only can't apply overrides

        if override.scope == OverrideScope.GLOBAL:
            return (
                permission_level == PermissionLevel.FULL_ADMIN
                and self.config.allow_global_overrides
            )

        return permission_level in [PermissionLevel.MODIFY, PermissionLevel.FULL_ADMIN]

    def _get_permission_level(self, developer_id: str) -> PermissionLevel:
        """Get permission level for a developer.

        Args:
            developer_id: Developer identifier

        Returns:
            Permission level
        """
        return self.config.developer_permissions.get(
            developer_id, self.config.default_permission_level
        )

    async def create_override(
        self,
        instructions: str,
        scope: OverrideScope,
        developer_id: str,
        user_id: str | None = None,
        conditions: dict[str, Any] | None = None,
        priority: int = None,
        expires_at: datetime | None = None,
        justification: str | None = None,
    ) -> str:
        """Create a new developer override.

        Args:
            instructions: Override instructions
            scope: Override scope
            developer_id: ID of developer creating the override
            user_id: Target user ID (for user-scoped overrides)
            conditions: Conditional logic
            priority: Override priority
            expires_at: Expiration timestamp
            justification: Justification for the override

        Returns:
            Override ID

        Raises:
            ValueError: If validation fails or permissions insufficient
        """
        # Validate permissions
        permission_level = self._get_permission_level(developer_id)
        if permission_level == PermissionLevel.NONE:
            raise ValueError(f"Developer {developer_id} has no override permissions")

        if permission_level == PermissionLevel.READ_ONLY:
            raise ValueError(f"Developer {developer_id} has read-only permissions")

        # Validate scope permissions
        if scope == OverrideScope.GLOBAL:
            if (
                permission_level != PermissionLevel.FULL_ADMIN
                or not self.config.allow_global_overrides
            ):
                raise ValueError("Global overrides require full admin permissions")

        # Validate instruction length
        if len(instructions) > self.config.max_instruction_length:
            raise ValueError(
                f"Instructions too long: {len(instructions)} > "
                f"{self.config.max_instruction_length}"
            )

        # Check if we're at max overrides
        if len(self._active_overrides) >= self.config.max_active_overrides:
            raise ValueError(
                f"Maximum active overrides reached: {self.config.max_active_overrides}"
            )

        # Validate expiration
        if not self.config.allow_permanent_overrides and expires_at is None:
            # Set default expiration of 24 hours
            expires_at = datetime.now().replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

        # Generate unique ID
        override_id = f"dev_override_{len(self._active_overrides)}_{int(datetime.now().timestamp())}"

        # Create override
        override = DeveloperOverride(
            id=override_id,
            instructions=instructions,
            scope=scope,
            user_id=user_id,
            conditions=conditions,
            created_by=developer_id,
            created_at=datetime.now(),
            expires_at=expires_at,
            priority=priority or self.config.default_override_priority,
            active=True,
        )

        # Store override
        self._active_overrides[override_id] = override
        await self._save_overrides_to_memory()

        # Log creation
        if self.config.enable_audit_trail:
            await self._log_audit_entry(
                "created",
                override_id,
                user_id or "all",
                developer_id,
                instructions,
                {
                    "scope": scope.value,
                    "priority": override.priority,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                    "justification": justification,
                },
            )

        logger.info(f"Created developer override {override_id} by {developer_id}")

        return override_id

    async def disable_override(self, override_id: str, developer_id: str) -> bool:
        """Disable an active override.

        Args:
            override_id: Override to disable
            developer_id: Developer disabling the override

        Returns:
            True if disabled successfully
        """
        if override_id not in self._active_overrides:
            return False

        override = self._active_overrides[override_id]

        # Check permissions
        permission_level = self._get_permission_level(developer_id)
        if permission_level not in [
            PermissionLevel.MODIFY,
            PermissionLevel.FULL_ADMIN,
        ] or (
            override.created_by != developer_id
            and permission_level != PermissionLevel.FULL_ADMIN
        ):
            raise ValueError("Insufficient permissions to disable override")

        # Disable override
        override.active = False
        await self._save_overrides_to_memory()

        # Log disable action
        if self.config.enable_audit_trail:
            await self._log_audit_entry(
                "disabled",
                override_id,
                override.user_id or "all",
                developer_id,
                override.instructions,
                {"reason": "manually_disabled"},
            )

        logger.info(f"Disabled developer override {override_id} by {developer_id}")

        return True

    async def list_overrides(
        self, developer_id: str, include_inactive: bool = False
    ) -> list[dict[str, Any]]:
        """List overrides visible to the developer.

        Args:
            developer_id: Developer requesting the list
            include_inactive: Whether to include inactive overrides

        Returns:
            List of override information
        """
        permission_level = self._get_permission_level(developer_id)
        if permission_level == PermissionLevel.NONE:
            return []

        overrides = []
        for override in self._active_overrides.values():
            if not include_inactive and not override.active:
                continue

            # Check if developer can see this override
            can_see = (
                permission_level == PermissionLevel.FULL_ADMIN
                or override.created_by == developer_id
            )

            if can_see:
                overrides.append(
                    {
                        "id": override.id,
                        "instructions": (
                            override.instructions[:100] + "..."
                            if len(override.instructions) > 100
                            else override.instructions
                        ),
                        "scope": override.scope.value,
                        "user_id": override.user_id,
                        "created_by": override.created_by,
                        "created_at": (
                            override.created_at.isoformat()
                            if override.created_at
                            else None
                        ),
                        "expires_at": (
                            override.expires_at.isoformat()
                            if override.expires_at
                            else None
                        ),
                        "priority": override.priority,
                        "active": override.active,
                    }
                )

        return sorted(overrides, key=lambda x: x["created_at"], reverse=True)

    async def _log_audit_entry(
        self,
        action: str,
        override_id: str,
        user_id: str,
        developer_id: str,
        instructions: str,
        context: dict[str, Any],
    ):
        """Log an audit entry.

        Args:
            action: Action performed
            override_id: Override ID
            user_id: Target user ID
            developer_id: Developer performing action
            instructions: Override instructions
            context: Additional context
        """
        entry = AuditEntry(
            timestamp=datetime.now(),
            override_id=override_id,
            user_id=user_id,
            developer_id=developer_id,
            action=action,
            instructions=instructions,
            context=context,
            result="success",  # Could be enhanced with actual result tracking
        )

        self._audit_trail.append(entry)

        # Save to memory for persistence
        memory_resource = self.resources.get("memory")
        if memory_resource:
            audit_key = f"{self.config.memory_key_prefix}_audit"
            try:
                await memory_resource.store(
                    audit_key,
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "override_id": entry.override_id,
                        "user_id": entry.user_id,
                        "developer_id": entry.developer_id,
                        "action": entry.action,
                        "instructions": entry.instructions[
                            :500
                        ],  # Truncate for storage
                        "context": entry.context,
                        "result": entry.result,
                    },
                )
            except Exception as e:
                logger.error(f"Failed to store audit entry: {e}")

    async def _save_overrides_to_memory(self):
        """Save active overrides to memory for persistence."""
        memory_resource = self.resources.get("memory")
        if not memory_resource:
            return

        try:
            overrides_data = {}
            for override_id, override in self._active_overrides.items():
                overrides_data[override_id] = {
                    "id": override.id,
                    "instructions": override.instructions,
                    "scope": override.scope.value,
                    "user_id": override.user_id,
                    "conditions": override.conditions,
                    "created_by": override.created_by,
                    "created_at": (
                        override.created_at.isoformat() if override.created_at else None
                    ),
                    "expires_at": (
                        override.expires_at.isoformat() if override.expires_at else None
                    ),
                    "priority": override.priority,
                    "active": override.active,
                }

            overrides_key = f"{self.config.memory_key_prefix}_overrides"
            await memory_resource.store(overrides_key, overrides_data)

        except Exception as e:
            logger.error(f"Failed to save overrides to memory: {e}")

    def _load_overrides_from_memory(self):
        """Load overrides from memory on initialization."""
        # This would be called during initialization
        # Implementation would load from memory resource
        # For now, we start with empty state
        pass

    def get_audit_trail(
        self,
        developer_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get audit trail entries.

        Args:
            developer_id: Developer requesting audit trail
            start_date: Filter start date
            end_date: Filter end date
            limit: Maximum entries to return

        Returns:
            List of audit entries
        """
        permission_level = self._get_permission_level(developer_id)
        if permission_level == PermissionLevel.NONE:
            return []

        # Filter entries
        entries = self._audit_trail

        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]

        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]

        # For non-admin users, only show their own actions
        if permission_level != PermissionLevel.FULL_ADMIN:
            entries = [e for e in entries if e.developer_id == developer_id]

        # Sort by timestamp (newest first) and limit
        entries = sorted(entries, key=lambda x: x.timestamp, reverse=True)[:limit]

        return [
            {
                "timestamp": entry.timestamp.isoformat(),
                "override_id": entry.override_id,
                "user_id": entry.user_id,
                "developer_id": entry.developer_id,
                "action": entry.action,
                "instructions": (
                    entry.instructions[:200] + "..."
                    if len(entry.instructions) > 200
                    else entry.instructions
                ),
                "context": entry.context,
                "result": entry.result,
            }
            for entry in entries
        ]

    async def cleanup_expired_overrides(self) -> int:
        """Clean up expired overrides.

        Returns:
            Number of overrides cleaned up
        """
        now = datetime.now()
        expired_count = 0

        for override_id, override in list(self._active_overrides.items()):
            if override.expires_at and now > override.expires_at:
                override.active = False
                expired_count += 1

                if self.config.enable_audit_trail:
                    await self._log_audit_entry(
                        "expired",
                        override_id,
                        override.user_id or "all",
                        "system",
                        override.instructions,
                        {"reason": "expired"},
                    )

        if expired_count > 0:
            await self._save_overrides_to_memory()
            logger.info(f"Cleaned up {expired_count} expired overrides")

        return expired_count
