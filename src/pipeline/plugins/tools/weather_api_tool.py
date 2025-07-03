from __future__ import annotations

from typing import Any, Dict

import httpx

from pipeline.base_plugins import ToolPlugin
from pipeline.stages import PipelineStage


class WeatherApiTool(ToolPlugin):
    """Fetch weather information from an external API.

    Shows **Distributed Tool Execution (25)** as each request is made only when
    needed and results are logged centrally.
    """

    stages = [PipelineStage.DO]
    required_params = ["location"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.base_url: str = self.config.get("base_url", "https://api.weather.com")
        self.api_key: str | None = self.config.get("api_key")
        self.timeout: int = int(self.config.get("timeout", 10))

    async def execute_function(self, params: Dict[str, Any]) -> Any:
        location = params.get("location")
        if not location:
            raise ValueError("'location' parameter is required")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    params={"location": location, "api_key": self.api_key},
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network error path
            raise RuntimeError(f"Weather request failed: {exc}") from exc

        return response.json()

    async def execute(self, params: Dict[str, Any]) -> Any:  # type: ignore[override]
        return await self.execute_function(params)
