from plugins.resources.dsl import ResourceGraph


def test_parse_and_validate():
    dsl = {
        "db": {"type": "pkg:Db"},
        "cache": {"type": "pkg:Cache", "depends_on": ["db"]},
    }
    graph = ResourceGraph.from_dict(dsl)
    assert set(graph.resources.keys()) == {"db", "cache"}
    dot = graph.to_dot()
    assert '"db" -> "cache"' in dot


def test_unknown_dependency():
    dsl = {"cache": {"type": "pkg:Cache", "depends_on": ["missing"]}}
    try:
        ResourceGraph.from_dict(dsl)
    except ValueError as exc:
        assert "unknown resource" in str(exc)
    else:
        raise AssertionError("expected error")
