"""Sphinx configuration for Entity documentation."""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../../src"))

# Mock modules that cause issues on ReadTheDocs
autodoc_mock_imports = [
    "aioboto3",
    "boto3",
    "botocore",
    "duckdb",
    "websockets",
    "grpcio",
    "grpcio-tools",
    "huggingface_hub",
    "httpx",
    "aiobotocore",
    "aiofiles",
    "s3transfer",
]

# Project information
project = "Entity"
copyright = f"{datetime.now().year}, C. Thomas Brittain"
author = "C. Thomas Brittain"
release = "0.0.1"
version = "0.0.1"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
]

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "httpx": ("https://www.python-httpx.org/", None),
}

# Add any paths that contain templates here
templates_path = ["_templates"]

# List of patterns to ignore when looking for source files
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# HTML output options
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = "Entity Documentation"
html_short_title = "Entity"
html_logo = None
html_favicon = None

# Enable todo extension
todo_include_todos = True

# Coverage extension
coverage_show_missing_items = True
