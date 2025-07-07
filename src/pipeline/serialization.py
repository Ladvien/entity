from __future__ import annotations

"""Helpers for efficient pipeline state serialization."""

import msgpack

from .state import PipelineState


def dumps_state(state: PipelineState) -> bytes:
    """Serialize ``state`` to msgpack-encoded bytes."""
    return msgpack.dumps(state.to_dict(), use_bin_type=True)


def loads_state(data: bytes) -> PipelineState:
    """Deserialize ``data`` into a :class:`PipelineState`."""
    return PipelineState.from_dict(msgpack.loads(data, raw=False))


__all__ = ["dumps_state", "loads_state"]
