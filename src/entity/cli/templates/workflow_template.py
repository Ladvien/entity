"""Template for workflow definition."""

from entity.pipeline import PipelineStage

WORKFLOW_NAME = {
    PipelineStage.INPUT: [],
    PipelineStage.PARSE: [],
    PipelineStage.THINK: [],
    PipelineStage.DO: [],
    PipelineStage.REVIEW: [],
    PipelineStage.OUTPUT: [],
}

# Replace ``WORKFLOW_NAME`` with your workflow variable name.
