import builtins
import importlib
import sys

import plugins.builtin.adapters as adapters


def test_import_without_grpc(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in {"grpc", "plugins.builtin.adapters.grpc"}:
            raise ImportError("grpc unavailable")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "plugins.builtin.adapters.grpc", raising=False)

    module = importlib.reload(adapters)

    assert module.LLMGRPCAdapter is None
    assert "LLMGRPCAdapter" not in module.__all__
