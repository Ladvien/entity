from __future__ import annotations

"""WebSocket adapter providing real-time interaction with the pipeline.

This module exposes :class:`WebSocketAdapter`, a FastAPI based adapter
that handles bi-directional communication over a WebSocket connection.
Each connected client can send messages to the pipeline and receive
JSON responses in return.
"""

from typing import Any, cast

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from pipeline.base_plugins import AdapterPlugin
from pipeline.exceptions import ResourceError
from pipeline.manager import PipelineManager
from pipeline.pipeline import execute_pipeline
from pipeline.security import AdapterAuthenticator
from pipeline.stages import PipelineStage
from registry import SystemRegistries


class WebSocketAdapter(AdapterPlugin):
    stages = [PipelineStage.DELIVER]
    """WebSocket adapter using FastAPI."""

    def __init__(
        self, manager: PipelineManager | None = None, config: dict | None = None
    ) -> None:
        super().__init__(config)
        self.manager = manager
        tokens_cfg = self.config.get("auth_tokens", [])
        if isinstance(tokens_cfg, list):
            mapping = {t: ["websocket"] for t in tokens_cfg}
        else:
            mapping = {str(k): v for k, v in dict(tokens_cfg).items()}
        self.authenticator = AdapterAuthenticator(mapping) if mapping else None
        self.app = FastAPI()
        self._registries: SystemRegistries | None = None
        self._setup_routes()

    async def _handle_message(self, message: str) -> dict[str, Any]:
        if self.manager is not None:
            return await self.manager.run_pipeline(message)
        if self._registries is None:
            raise ResourceError("Adapter not initialized")
        return cast(dict[str, Any], await execute_pipeline(message, self._registries))

    async def _connection_handler(self, websocket: WebSocket) -> None:
        """Handle a single client WebSocket connection.

        Parameters
        ----------
        websocket:
            The accepted WebSocket connection from FastAPI.
        """
        if self.authenticator is not None:
            token = websocket.headers.get("authorization")
            token = token.split(" ")[-1] if token and " " in token else token
            if not self.authenticator.authenticate(
                token
            ) or not self.authenticator.authorize(token, "websocket"):
                await websocket.close(code=1008)
                return
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                response = await self._handle_message(data)
                await websocket.send_json(response)
        except WebSocketDisconnect:  # client closed connection
            await websocket.close()
        except Exception:  # pragma: no cover - adapter
            await websocket.close()
            raise

    def _setup_routes(self) -> None:
        self.app.add_api_websocket_route("/", self._connection_handler)

    async def serve(self, registries: SystemRegistries) -> None:
        """Start the FastAPI WebSocket server.

        Parameters
        ----------
        registries:
            System registries containing all initialized plugins and resources.
        """
        self._registries = registries
        host = self.config.get("host", "127.0.0.1")
        port = int(self.config.get("port", 8001))
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def _execute_impl(self, context) -> None:  # pragma: no cover - adapter
        pass
