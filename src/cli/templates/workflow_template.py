"""Template for workflow definition."""

from pipeline import PipelineStage

{workflow_name} = {
    PipelineStage.PARSE: [],
    PipelineStage.THINK: [],
    PipelineStage.DO: [],
    PipelineStage.DELIVER: [],
}
