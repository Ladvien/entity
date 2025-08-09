"""Developer Override Plugin for GPT-OSS integration.

This plugin leverages harmony's developer role to inject behavior modifications
that override system prompts safely, allowing prompt engineers to fine-tune
agent behavior without modifying base configurations.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from entity.plugins.base import Plugin
from entity.workflow.executor import WorkflowExecutor


class DeveloperRoleLevel(Enum):
    """Developer role access levels."""

    NONE = "none"
    READ = "read"
    OVERRIDE = "override"
    ADMIN = "admin"


class DeveloperOverrideType(Enum):
    """Types of developer overrides available."""

    SYSTEM_PROMPT = "system_prompt"
    BEHAVIOR_MODIFICATION = "behavior_modification"
    CONSTRAINT_OVERRIDE = "constraint_override"
    REASONING_ADJUSTMENT = "reasoning_adjustment"
    OUTPUT_FORMAT = "output_format"


class DeveloperOverride(BaseModel):
    """A single developer override instruction."""

    override_id: str = Field(description="Unique identifier for this override")
    override_type: DeveloperOverrideType = Field(description="Type of override")
    content: str = Field(description="Override instruction content")
    priority: int = Field(
        default=1,
        description="Override priority (higher = more important)",
        ge=1,
        le=10,
    )
    conditions: Dict[str, Any] = Field(
        default_factory=dict, description="Conditions for applying override"
    )
    created_by: str = Field(description="User who created this override")
    created_at: datetime = Field(default_factory=datetime.now)
    active: bool = Field(default=True, description="Whether override is active")
    description: str = Field(
        default="", description="Human-readable description of override"
    )


class DeveloperOverrideAuditEntry(BaseModel):
    """Audit trail entry for developer override usage."""

    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: str = Field(description="User who triggered the override")
    override_id: str = Field(description="ID of applied override")
    override_type: DeveloperOverrideType = Field(description="Type of override applied")
    original_message: str = Field(description="Original user message")
    modified_message: str = Field(description="Message after override application")
    success: bool = Field(description="Whether override was successfully applied")
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )


class DeveloperOverridePlugin(Plugin):
    """Plugin that implements developer role overrides in the PARSE stage.

    This plugin:
    - Supports developer role injection using harmony format
    - Maintains role hierarchy (developer > user)
    - Allows runtime behavior modification
    - Provides comprehensive audit trail
    - Implements permission system for developer access
    - Integrates with Entity's configuration system
    """

    supported_stages = [WorkflowExecutor.PARSE]
    dependencies = ["llm", "memory"]

    class ConfigModel(BaseModel):
        """Configuration for the developer override plugin."""

        # Permission settings
        enable_developer_overrides: bool = Field(
            default=True, description="Enable developer override functionality"
        )
        developer_permission_level: DeveloperRoleLevel = Field(
            default=DeveloperRoleLevel.READ,
            description="Default developer permission level",
        )
        authorized_developers: List[str] = Field(
            default_factory=list, description="List of authorized developer user IDs"
        )
        admin_users: List[str] = Field(
            default_factory=list, description="List of admin user IDs with full access"
        )

        # Override behavior
        max_active_overrides: int = Field(
            default=5,
            description="Maximum number of active overrides per user",
            ge=1,
            le=20,
        )
        override_priority_threshold: int = Field(
            default=1,
            description="Minimum priority for overrides to be applied",
            ge=1,
            le=10,
        )
        allow_system_prompt_override: bool = Field(
            default=False, description="Allow overriding system prompts (dangerous)"
        )
        require_override_description: bool = Field(
            default=True, description="Require description for all overrides"
        )

        # Audit and logging
        enable_audit_trail: bool = Field(
            default=True, description="Enable audit trail for overrides"
        )
        audit_retention_days: int = Field(
            default=30, description="Days to retain audit entries", ge=1, le=365
        )
        log_override_content: bool = Field(
            default=False, description="Log full override content (privacy concern)"
        )

        # Integration settings
        persist_overrides: bool = Field(
            default=True, description="Persist overrides across sessions"
        )
        broadcast_overrides: bool = Field(
            default=False, description="Apply overrides to all users (admin only)"
        )

    def __init__(self, resources: dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize the developer override plugin."""
        super().__init__(resources, config)

        # Validate configuration
        validation_result = self.validate_config()
        if not validation_result.success:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")

        # Initialize internal state
        self.active_overrides: Dict[str, List[DeveloperOverride]] = {}
        self.audit_entries: List[DeveloperOverrideAuditEntry] = []

    async def _execute_impl(self, context) -> str:
        """Execute developer override logic in PARSE stage."""
        if not self.config.enable_developer_overrides:
            # Plugin disabled, pass through
            return context.message

        user_id = context.user_id
        original_message = context.message

        try:
            # Check developer permissions
            permission_level = await self._get_developer_permission_level(user_id)
            if permission_level == DeveloperRoleLevel.NONE:
                # User has no developer permissions, pass through
                return original_message

            # Load active overrides for this user
            active_overrides = await self._load_active_overrides(user_id)

            if not active_overrides:
                # No active overrides, pass through
                return original_message

            # Apply overrides in priority order
            modified_message = await self._apply_overrides(
                context, original_message, active_overrides, permission_level
            )

            # Create audit entry
            if self.config.enable_audit_trail:
                await self._create_audit_entry(
                    user_id=user_id,
                    overrides_applied=active_overrides,
                    original_message=original_message,
                    modified_message=modified_message,
                    success=True,
                )

            # Log override application
            await context.log(
                level="info",
                category="developer_override",
                message=f"Applied {len(active_overrides)} developer overrides",
                user_id=user_id,
                permission_level=permission_level.value,
                overrides_count=len(active_overrides),
            )

            return modified_message

        except Exception as e:
            # Log error and create audit entry
            await context.log(
                level="error",
                category="developer_override",
                message=f"Error applying developer overrides: {str(e)}",
                user_id=user_id,
                error=str(e),
            )

            if self.config.enable_audit_trail:
                await self._create_audit_entry(
                    user_id=user_id,
                    overrides_applied=[],
                    original_message=original_message,
                    modified_message=original_message,
                    success=False,
                    error_message=str(e),
                )

            # On error, return original message
            return original_message

    async def _get_developer_permission_level(self, user_id: str) -> DeveloperRoleLevel:
        """Get the developer permission level for a user."""
        # Check if user is admin
        if user_id in self.config.admin_users:
            return DeveloperRoleLevel.ADMIN

        # Check if user is authorized developer
        if user_id in self.config.authorized_developers:
            return DeveloperRoleLevel.OVERRIDE

        # Check for stored permission level
        stored_level = await self.resources["memory"].load(
            f"dev_permission:{user_id}", None
        )
        if stored_level:
            try:
                return DeveloperRoleLevel(stored_level)
            except ValueError:
                pass

        # Default to configured level
        return self.config.developer_permission_level

    async def _load_active_overrides(self, user_id: str) -> List[DeveloperOverride]:
        """Load active overrides for a user."""
        if not self.config.persist_overrides:
            return self.active_overrides.get(user_id, [])

        # Load from memory
        stored_overrides = await self.resources["memory"].load(
            f"dev_overrides:{user_id}", []
        )

        overrides = []
        for override_data in stored_overrides:
            try:
                if isinstance(override_data, dict):
                    override = DeveloperOverride(**override_data)
                    if override.active:
                        overrides.append(override)
            except Exception as e:
                # Log invalid override and skip
                await self.resources["logging"].log(
                    "warning",
                    "developer_override",
                    f"Skipping invalid override: {str(e)}",
                    user_id=user_id,
                    override_data=str(override_data)[:100],
                )

        # Sort by priority (highest first)
        overrides.sort(key=lambda x: x.priority, reverse=True)

        # Apply max overrides limit
        if len(overrides) > self.config.max_active_overrides:
            overrides = overrides[: self.config.max_active_overrides]

        return overrides

    async def _apply_overrides(
        self,
        context,
        message: str,
        overrides: List[DeveloperOverride],
        permission_level: DeveloperRoleLevel,
    ) -> str:
        """Apply developer overrides to the message."""
        modified_message = message

        for override in overrides:
            # Check permission level for this override type
            if not self._can_apply_override(override, permission_level):
                await context.log(
                    level="warning",
                    category="developer_override",
                    message=f"Insufficient permissions for override {override.override_id}",
                    override_type=override.override_type.value,
                    required_level=(
                        "admin"
                        if override.override_type == DeveloperOverrideType.SYSTEM_PROMPT
                        else "override"
                    ),
                )
                continue

            # Check priority threshold
            if override.priority < self.config.override_priority_threshold:
                continue

            # Check conditions
            if not await self._evaluate_override_conditions(
                context, override.conditions
            ):
                continue

            # Apply the override
            try:
                modified_message = await self._apply_single_override(
                    context, modified_message, override
                )
            except Exception as e:
                await context.log(
                    level="error",
                    category="developer_override",
                    message=f"Failed to apply override {override.override_id}: {str(e)}",
                    override_type=override.override_type.value,
                    error=str(e),
                )

        return modified_message

    def _can_apply_override(
        self, override: DeveloperOverride, permission_level: DeveloperRoleLevel
    ) -> bool:
        """Check if user has permission to apply this override."""
        if permission_level == DeveloperRoleLevel.ADMIN:
            return True

        if permission_level == DeveloperRoleLevel.OVERRIDE:
            # Regular developers can't override system prompts unless explicitly allowed
            if (
                override.override_type == DeveloperOverrideType.SYSTEM_PROMPT
                and not self.config.allow_system_prompt_override
            ):
                return False
            return True

        return False

    async def _evaluate_override_conditions(
        self, context, conditions: Dict[str, Any]
    ) -> bool:
        """Evaluate whether override conditions are met."""
        if not conditions:
            return True

        # Example conditions:
        # - message_contains: "specific text"
        # - message_length_gt: 100
        # - user_role: "admin"
        # - time_of_day: "business_hours"

        message = context.message.lower()

        if "message_contains" in conditions:
            required_text = conditions["message_contains"].lower()
            if required_text not in message:
                return False

        if "message_length_gt" in conditions:
            if len(context.message) <= conditions["message_length_gt"]:
                return False

        if "message_length_lt" in conditions:
            if len(context.message) >= conditions["message_length_lt"]:
                return False

        # Add more condition types as needed
        return True

    async def _apply_single_override(
        self, context, message: str, override: DeveloperOverride
    ) -> str:
        """Apply a single override to the message."""
        override_type = override.override_type
        content = override.content

        if override_type == DeveloperOverrideType.BEHAVIOR_MODIFICATION:
            # Inject developer instructions into the message
            developer_instruction = f"\n\n[DEVELOPER]: {content}\n\n"
            return message + developer_instruction

        elif override_type == DeveloperOverrideType.SYSTEM_PROMPT:
            # This would typically modify the system message, not user message
            # For now, we'll add it as a developer instruction
            system_override = f"\n\n[SYSTEM_OVERRIDE]: {content}\n\n"
            return system_override + message

        elif override_type == DeveloperOverrideType.CONSTRAINT_OVERRIDE:
            # Add constraint modifications
            constraint_instruction = f"\n\n[CONSTRAINTS]: {content}\n\n"
            return message + constraint_instruction

        elif override_type == DeveloperOverrideType.REASONING_ADJUSTMENT:
            # Add reasoning level adjustments
            reasoning_instruction = f"\n\n[REASONING]: {content}\n\n"
            return message + reasoning_instruction

        elif override_type == DeveloperOverrideType.OUTPUT_FORMAT:
            # Add output format instructions
            format_instruction = f"\n\n[OUTPUT_FORMAT]: {content}\n\n"
            return message + format_instruction

        else:
            # Unknown override type, log and skip
            await context.log(
                level="warning",
                category="developer_override",
                message=f"Unknown override type: {override_type}",
                override_id=override.override_id,
            )
            return message

    async def _create_audit_entry(
        self,
        user_id: str,
        overrides_applied: List[DeveloperOverride],
        original_message: str,
        modified_message: str,
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """Create an audit trail entry."""
        for override in overrides_applied:
            entry = DeveloperOverrideAuditEntry(
                user_id=user_id,
                override_id=override.override_id,
                override_type=override.override_type,
                original_message=(
                    original_message
                    if self.config.log_override_content
                    else "[REDACTED]"
                ),
                modified_message=(
                    modified_message
                    if self.config.log_override_content
                    else "[REDACTED]"
                ),
                success=success,
                error_message=error_message,
            )

            # Store audit entry
            audit_key = f"audit_trail:{user_id}:{datetime.now().strftime('%Y%m%d')}"
            existing_entries = await self.resources["memory"].load(audit_key, [])
            existing_entries.append(entry.model_dump())
            await self.resources["memory"].store(audit_key, existing_entries)

    # Public API methods for managing overrides

    async def add_override(
        self,
        user_id: str,
        override_type: DeveloperOverrideType,
        content: str,
        priority: int = 1,
        conditions: Dict[str, Any] = None,
        description: str = "",
    ) -> str:
        """Add a new developer override."""
        if conditions is None:
            conditions = {}

        # Validate description requirement
        if self.config.require_override_description and not description:
            raise ValueError("Override description is required")

        # Generate override ID
        override_id = f"{user_id}_{override_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create override
        override = DeveloperOverride(
            override_id=override_id,
            override_type=override_type,
            content=content,
            priority=priority,
            conditions=conditions,
            created_by=user_id,
            description=description,
        )

        # Store override
        if self.config.persist_overrides:
            stored_overrides = await self.resources["memory"].load(
                f"dev_overrides:{user_id}", []
            )
            stored_overrides.append(override.model_dump())
            await self.resources["memory"].store(
                f"dev_overrides:{user_id}", stored_overrides
            )
        else:
            if user_id not in self.active_overrides:
                self.active_overrides[user_id] = []
            self.active_overrides[user_id].append(override)

        return override_id

    async def remove_override(self, user_id: str, override_id: str) -> bool:
        """Remove a developer override."""
        if self.config.persist_overrides:
            stored_overrides = await self.resources["memory"].load(
                f"dev_overrides:{user_id}", []
            )
            original_count = len(stored_overrides)
            stored_overrides = [
                o for o in stored_overrides if o.get("override_id") != override_id
            ]
            if len(stored_overrides) < original_count:
                await self.resources["memory"].store(
                    f"dev_overrides:{user_id}", stored_overrides
                )
                return True
        else:
            if user_id in self.active_overrides:
                original_count = len(self.active_overrides[user_id])
                self.active_overrides[user_id] = [
                    o
                    for o in self.active_overrides[user_id]
                    if o.override_id != override_id
                ]
                return len(self.active_overrides[user_id]) < original_count

        return False

    async def list_overrides(self, user_id: str) -> List[Dict[str, Any]]:
        """List all overrides for a user."""
        overrides = await self._load_active_overrides(user_id)
        return [
            {
                "override_id": o.override_id,
                "override_type": o.override_type.value,
                "priority": o.priority,
                "active": o.active,
                "description": o.description,
                "created_at": o.created_at.isoformat(),
                "conditions": o.conditions,
            }
            for o in overrides
        ]

    async def get_audit_trail(
        self, user_id: str, days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a user."""
        if not self.config.enable_audit_trail:
            return []

        entries = []
        for i in range(days):
            date_key = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
            audit_key = f"audit_trail:{user_id}:{date_key}"
            daily_entries = await self.resources["memory"].load(audit_key, [])
            entries.extend(daily_entries)

        return entries

    async def set_developer_permission(
        self,
        admin_user_id: str,
        target_user_id: str,
        permission_level: DeveloperRoleLevel,
    ) -> bool:
        """Set developer permission for a user (admin only)."""
        admin_level = await self._get_developer_permission_level(admin_user_id)
        if admin_level != DeveloperRoleLevel.ADMIN:
            raise PermissionError("Only admin users can modify permissions")

        await self.resources["memory"].store(
            f"dev_permission:{target_user_id}", permission_level.value
        )
        return True
