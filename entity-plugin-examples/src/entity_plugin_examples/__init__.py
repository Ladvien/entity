"""Entity Framework Example Plugins - Educational and demonstration plugins."""

from entity_plugin_examples.calculator import CalculatorPlugin
from entity_plugin_examples.input_reader import InputReaderPlugin
from entity_plugin_examples.keyword_extractor import KeywordExtractorPlugin
from entity_plugin_examples.output_formatter import OutputFormatterPlugin
from entity_plugin_examples.reason_generator import ReasonGeneratorPlugin
from entity_plugin_examples.static_reviewer import StaticReviewerPlugin
from entity_plugin_examples.typed_example_plugin import TypedExamplePlugin

__all__ = [
    "CalculatorPlugin",
    "InputReaderPlugin",
    "KeywordExtractorPlugin",
    "OutputFormatterPlugin",
    "ReasonGeneratorPlugin",
    "StaticReviewerPlugin",
    "TypedExamplePlugin",
]

__version__ = "0.1.0"
