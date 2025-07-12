"""Template for workflow definition."""

from pipeline import PipelineStage

{workflow_name} = {
    PipelineStage.INPUT: [],
    PipelineStage.PARSE: [],
    PipelineStage.THINK: [],
    PipelineStage.DO: [],
    PipelineStage.REVIEW: [],
    PipelineStage.OUTPUT: [],
}
