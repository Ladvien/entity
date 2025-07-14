from entity.core.plugins import ResourcePlugin


class DummyResource(ResourcePlugin):
    """Simple resource for observability injection test."""

    stages: list = []
    infrastructure_dependencies: list[str] = []
    dependencies: list[str] = []


def test_resource_plugin_has_no_observability_dependencies() -> None:
    assert "logging" not in DummyResource.dependencies
    assert "metrics_collector" not in DummyResource.dependencies
