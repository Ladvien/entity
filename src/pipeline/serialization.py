from __future__ import annotations

"""Helpers for efficient pipeline state serialization."""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime

import msgpack

from .state import PipelineState


def dumps_state(state: PipelineState) -> bytes:
    """Serialize ``state`` to msgpack-encoded bytes."""
    return msgpack.dumps(state.to_dict(), use_bin_type=True)


def loads_state(data: bytes) -> PipelineState:
    """Deserialize ``data`` into a :class:`PipelineState`."""
    return PipelineState.from_dict(msgpack.loads(data, raw=False))


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def dumps_json(obj: object) -> str:
    """Serialize ``obj`` to JSON using dataclass support."""
    if is_dataclass(obj):
        obj = asdict(obj)
    return json.dumps(obj, default=_json_default)


def loads_json(data: str) -> object:
    """Deserialize ``data`` from JSON."""
    return json.loads(data)


__all__ = [
    "dumps_state",
    "loads_state",
    "dumps_json",
    "loads_json",
]
