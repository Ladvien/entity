from __future__ import annotations

"""Helpers for efficient pipeline state serialization."""

import json
from dataclasses import asdict, is_dataclass
from typing import Any

import msgpack

from .state import PipelineState


def dumps_state(state: PipelineState) -> bytes:
    """Serialize ``state`` to msgpack-encoded bytes."""
    return msgpack.dumps(state.to_dict(), use_bin_type=True)


def loads_state(data: bytes) -> PipelineState:
    """Deserialize ``data`` into a :class:`PipelineState`."""
    return PipelineState.from_dict(msgpack.loads(data, raw=False))


def dumps_json(obj: Any) -> str:
    """Serialize ``obj`` to JSON, handling dataclasses."""
    if is_dataclass(obj):
        obj = asdict(obj)
    return json.dumps(obj)


def loads_json(data: str, cls: type | None = None) -> Any:
    """Deserialize ``data`` to ``cls`` or a plain object."""
    obj = json.loads(data)
    if cls is not None:
        if is_dataclass(cls):
            return cls(**obj)
        return cls(obj)
    return obj


__all__ = ["dumps_state", "loads_state", "dumps_json", "loads_json"]
