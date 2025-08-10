"""Workflow stage constants.

This module defines the standard workflow stages to avoid circular imports.
"""

# Standard workflow stages
INPUT = "input"
PARSE = "parse"
THINK = "think"
DO = "do"
REVIEW = "review"
OUTPUT = "output"
ERROR = "error"

# Stage execution order
STAGE_ORDER = [INPUT, PARSE, THINK, DO, REVIEW, OUTPUT]
ALL_STAGES = STAGE_ORDER + [ERROR]
