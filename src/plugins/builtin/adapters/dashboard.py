from __future__ import annotations

"""HTTP dashboard adapter."""

import json
from collections import deque
from pathlib import Path
from typing import Any

from pipeline.manager import PipelineManager

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pipeline.stages import PipelineStage
from plugins.builtin.adapters.http import HTTPAdapter
from tools.pipeline_viz import PipelineGraphBuilder


class DashboardAdapter(HTTPAdapter):
    """HTTP adapter with a simple status dashboard."""

    def __init__(
        self,
        manager: PipelineManager[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(manager, config)
        templates_dir = Path(__file__).parent / "templates"
        self.templates = Jinja2Templates(directory=str(templates_dir))
        self.state_log_path = Path(self.config.get("state_log_path", "state.log"))
        self.pipeline_config = self.config.get("pipeline_config")

    def _setup_routes(self) -> None:
        super()._setup_routes()
        if not self.dashboard_enabled:
            return

        @self.app.get("/dashboard", response_class=HTMLResponse)  # type: ignore[misc]
        async def dashboard(request: Request) -> HTMLResponse:
            count = 0
            if self.manager is not None:
                count = self.manager.active_pipeline_count()
            graph = self._render_graph()
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "active_pipelines": count,
                    "graph": graph,
                },
            )

        @self.app.get("/dashboard/transitions")  # type: ignore[misc]
        async def transitions(limit: int = 50) -> list[dict[str, Any]]:
            return self._load_transitions(limit)

    def _load_transitions(self, limit: int) -> list[dict[str, Any]]:
        if not self.state_log_path.exists():
            return []
        with self.state_log_path.open("r", encoding="utf-8") as handle:
            items = deque(handle, maxlen=limit)
        return [json.loads(line) for line in items]

    def _render_graph(self) -> str:
        if not self.pipeline_config:
            return ""
        builder = PipelineGraphBuilder(self.pipeline_config)
        graph = builder.build()
        lines = ["graph LR"]
        prev = None
        for stage in PipelineStage:
            if stage == PipelineStage.ERROR:
                continue
            lines.append(f"{stage.name}[{stage.name}]")
            if prev is not None:
                lines.append(f"{prev.name} --> {stage.name}")
            prev = stage
            for plugin in graph._mapping.get(stage, []):
                lines.append(f"{stage.name} -.-> {plugin}")
        return "\n".join(lines)
