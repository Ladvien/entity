from __future__ import annotations

import asyncio
import inspect

from cli.plugin_tool.utils import load_plugin


class DummyContext:
    async def __getattr__(self, _name: str):
        async def _noop(*_a, **_kw):
            return None

        return _noop


def run_plugin(path: str) -> None:
    async def _runner() -> None:
        plugin_cls = load_plugin(path)
        instance = plugin_cls(getattr(plugin_cls, "config", {}))
        init = getattr(instance, "initialize", None)
        if callable(init):
            if inspect.iscoroutinefunction(init):
                await init()
            else:
                init()
        execute = getattr(instance, "_execute_impl", None)
        if callable(execute):
            ctx = DummyContext()
            if inspect.iscoroutinefunction(execute):
                await execute(ctx)
            else:
                execute(ctx)

    asyncio.run(_runner())
