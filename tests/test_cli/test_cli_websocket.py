import sys

import sys
from pathlib import Path

from plugins.builtin.adapters.websocket import WebSocketAdapter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from entity.cli import EntityCLI as CLI


def test_cli_websocket(monkeypatch, tmp_path):
    config = tmp_path / "cfg.yml"
    config.write_text("")
    called = False

    async def fake_serve(self, capabilities):
        nonlocal called
        called = True

    monkeypatch.setattr(WebSocketAdapter, "serve", fake_serve)
    monkeypatch.setattr(
        sys, "argv", ["prog", "--config", str(config), "serve-websocket"]
    )

    CLI().run()

    assert called
