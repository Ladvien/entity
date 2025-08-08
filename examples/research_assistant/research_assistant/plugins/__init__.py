"""Research Assistant Plugins."""

from .input_plugins import MultiModalInputPlugin
from .parser_plugins import QueryParserPlugin, EntityExtractorPlugin
from .thinking_plugins import ResearchPlannerPlugin
from .tool_plugins import (
    ArxivSearchPlugin,
    WebSearchPlugin,
    PDFAnalyzerPlugin,
    SemanticScholarPlugin,
    DataVisualizerPlugin,
)
from .review_plugins import (
    FactCheckerPlugin,
    CitationValidatorPlugin,
    QualityAssurancePlugin,
)
from .output_plugins import ReportGeneratorPlugin

__all__ = [
    "MultiModalInputPlugin",
    "QueryParserPlugin",
    "EntityExtractorPlugin", 
    "ResearchPlannerPlugin",
    "ArxivSearchPlugin",
    "WebSearchPlugin",
    "PDFAnalyzerPlugin",
    "SemanticScholarPlugin",
    "DataVisualizerPlugin",
    "FactCheckerPlugin",
    "CitationValidatorPlugin",
    "QualityAssurancePlugin",
    "ReportGeneratorPlugin",
]