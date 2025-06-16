# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "listening_neuron"
copyright = "2025, C. Thomas Brittain"
author = "C. Thomas Brittain"
release = "0.0.29"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",  # Allows Markdown files
    "sphinx.ext.autosectionlabel",  # Adds links to different sections of document
    "autodoc2",
]


templates_path = ["_templates"]
exclude_patterns = []

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

# https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html
# autoapi_dirs = ['../../listening_neuron']
autodoc2_packages = ["../../listening_neuron"]
