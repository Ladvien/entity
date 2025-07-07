from dataclasses import dataclass

from pipeline.serialization import dumps_json, loads_json


@dataclass
class Sample:
    x: int
    y: str


def test_dumps_json_handles_dataclass():
    obj = Sample(1, "a")
    data = dumps_json(obj)
    assert data == '{"x": 1, "y": "a"}'


def test_loads_json_round_trip_dataclass():
    obj = Sample(2, "b")
    data = dumps_json(obj)
    loaded = loads_json(data, Sample)
    assert loaded == obj


def test_loads_json_default_to_dict():
    obj = {"k": "v"}
    data = dumps_json(obj)
    assert loads_json(data) == obj
