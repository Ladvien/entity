"""Benchmark common serialization formats."""

from __future__ import annotations

import json
import pickle
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable

import msgpack
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct


class Serializer:
    """Base serializer."""

    name: str

    def dumps(self, data: Any) -> bytes:  # pragma: no cover - simple wrappers
        raise NotImplementedError

    def loads(self, data: bytes) -> Any:  # pragma: no cover - simple wrappers
        raise NotImplementedError


class PickleSerializer(Serializer):
    name = "pickle"

    def dumps(self, data: Any) -> bytes:
        return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

    def loads(self, data: bytes) -> Any:
        return pickle.loads(data)


class JsonSerializer(Serializer):
    name = "json"

    def dumps(self, data: Any) -> bytes:
        return json.dumps(data).encode()

    def loads(self, data: bytes) -> Any:
        return json.loads(data.decode())


class MsgpackSerializer(Serializer):
    name = "msgpack"

    def dumps(self, data: Any) -> bytes:
        return msgpack.dumps(data)

    def loads(self, data: bytes) -> Any:
        return msgpack.loads(data)


class ProtobufSerializer(Serializer):
    name = "protobuf"

    def dumps(self, data: Any) -> bytes:
        struct = Struct()
        struct.update(data)
        return struct.SerializeToString()

    def loads(self, data: bytes) -> Any:
        struct = Struct()
        struct.ParseFromString(data)
        return MessageToDict(struct)


def time_call(fn: Callable[[], Any], repeats: int) -> float:
    start = time.perf_counter()
    for _ in range(repeats):
        fn()
    return time.perf_counter() - start


@dataclass
class BenchmarkResult:
    serializer: str
    size: int
    serialize_time: float
    deserialize_time: float


class SerializationBenchmark:
    """Measure serialization performance."""

    def __init__(self, data: Any, loops: int = 1000) -> None:
        self.data = data
        self.loops = loops
        self.serializers: Iterable[Serializer] = [
            PickleSerializer(),
            JsonSerializer(),
            MsgpackSerializer(),
            ProtobufSerializer(),
        ]

    def run(self) -> list[BenchmarkResult]:
        results: list[BenchmarkResult] = []
        for ser in self.serializers:
            b = ser.dumps(self.data)
            s_time = time_call(lambda: ser.dumps(self.data), self.loops)
            d_time = time_call(lambda: ser.loads(b), self.loops)
            results.append(BenchmarkResult(ser.name, len(b), s_time, d_time))
        return results


if __name__ == "__main__":
    payload = [{"id": i, "text": f"value-{i}"} for i in range(1000)]
    bench = SerializationBenchmark(payload)
    for result in bench.run():
        print(
            f"{result.serializer}\t{result.size}\t"
            f"{result.serialize_time:.4f}s\t{result.deserialize_time:.4f}s"
        )
