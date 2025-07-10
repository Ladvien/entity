from __future__ import annotations

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx


class PluginVisualizerDirective(Directive):
    has_content = False

    def run(self) -> list[nodes.Node]:
        return [nodes.raw("", '<div id="plugin-visualizer"></div>', format="html")]


def setup(app: Sphinx) -> dict[str, str | bool | int]:
    app.add_js_file("https://unpkg.com/react@18/umd/react.development.js")
    app.add_js_file("https://unpkg.com/react-dom@18/umd/react-dom.development.js")
    app.add_css_file("plugin_visualizer.css")
    app.add_js_file("plugin_visualizer.js")
    app.add_directive("plugin-visualizer", PluginVisualizerDirective)
    return {"version": "0.1"}
