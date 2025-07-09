from __future__ import annotations

"""Entity-specific plugin context."""

from typing import Any

from pipeline.context import PluginContext as _BaseContext
from pipeline.stages import PipelineStage


class PluginContext(_BaseContext):
    """Extend base context with stricter response handling."""

    def set_response(self, response: Any) -> None:  # noqa: D401 - clear override
        """Finalize ``response`` only during the DELIVER stage."""
        if self.current_stage != PipelineStage.DELIVER:
            raise ValueError("Only DELIVER stage plugins may set responses")
        super().set_response(response)


__all__ = ["PluginContext"]
