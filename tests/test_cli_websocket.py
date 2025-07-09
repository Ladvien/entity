import sys

from plugins.builtin.adapters.websocket import WebSocketAdapter

from cli import CLI


def test_cli_websocket(monkeypatch, tmp_path):
    config = tmp_path / "cfg.yml"
    config.write_text("")
    called = False

    async def fake_serve(self, registries):
        nonlocal called
        called = True

    monkeypatch.setattr(WebSocketAdapter, "serve", fake_serve)
    monkeypatch.setattr(
        sys, "argv", ["prog", "--config", str(config), "serve-websocket"]
    )

    CLI().run()

    assert called
