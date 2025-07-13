"""Template for workflow definition."""

from entity.pipeline import PipelineStage

{workflow_name} = {
    PipelineStage.INPUT: [],
    PipelineStage.PARSE: [],
    PipelineStage.THINK: [],
    PipelineStage.DO: [],
    PipelineStage.REVIEW: [],
    PipelineStage.OUTPUT: [],
}
