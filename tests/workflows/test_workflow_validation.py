import pytest

pipeline = pytest.importorskip("pipeline")

validate_topology = getattr(pipeline, "validate_topology", None)
if validate_topology is None:
    pytest.skip("validate_topology not available", allow_module_level=True)

PipelineStage = pipeline.PipelineStage


def test_invalid_stage_mapping_raises_error():
    invalid = {"NOT_A_STAGE": ["noop"]}
    with pytest.raises(Exception):
        validate_topology(invalid)
