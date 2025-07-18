from __future__ import annotations

import asyncio
import inspect

from entity.core.plugins import Plugin
from entity.cli import load_plugin


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
        ctx = DummyContext()
        if (
            callable(execute)
            and getattr(execute, "__func__", None) is not Plugin._execute_impl
        ):
            if inspect.iscoroutinefunction(execute):
                await execute(ctx)
            else:
                execute(ctx)
        else:
            tool_call = getattr(instance, "execute_function", None)
            if callable(tool_call):
                if inspect.iscoroutinefunction(tool_call):
                    await tool_call({})
                else:
                    tool_call({})

    asyncio.run(_runner())
