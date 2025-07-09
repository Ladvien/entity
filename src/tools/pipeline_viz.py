from __future__ import annotations

"""Generate a Graphviz DOT diagram of the pipeline."""

from collections import defaultdict
from typing import Dict, List

import yaml

from pipeline.interfaces import import_plugin_class
from pipeline.stages import PipelineStage


class PipelineGraph:
    """Simple representation of stage -> plugin mappings."""

    def __init__(self) -> None:
        self._mapping: Dict[PipelineStage, List[str]] = defaultdict(list)

    def add(self, stage: PipelineStage, plugin: str) -> None:
        self._mapping[stage].append(plugin)

    def to_dot(self) -> str:
        lines = ["digraph pipeline {", "    rankdir=LR;"]
        prev = None
        for stage in PipelineStage:
            if stage == PipelineStage.ERROR:
                continue
            lines.append(f'    "{stage.name}" [shape=ellipse];')
            if prev is not None:
                lines.append(f'    "{prev.name}" -> "{stage.name}";')
            prev = stage
            for plugin in self._mapping.get(stage, []):
                lines.append(f'    "{stage.name}" -> "{plugin}" [style=dashed];')
        lines.append("}")
        return "\n".join(lines)


class PipelineGraphBuilder:
    """Load plugin stages from a YAML config file."""

    def __init__(self, path: str) -> None:
        self.path = path

    def build(self) -> PipelineGraph:
        with open(self.path, "r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
        graph = PipelineGraph()
        plugins_cfg = cfg.get("plugins", {})
        for section in ("prompts", "adapters", "tools"):
            for name, pcfg in plugins_cfg.get(section, {}).items():
                cls_path = pcfg.get("type")
                if not cls_path:
                    continue
                cls = import_plugin_class(cls_path)
                for stage in getattr(cls, "stages", []):
                    graph.add(PipelineStage.ensure(stage), name)
        return graph


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate pipeline graph")
    parser.add_argument("config", help="Path to YAML config")
    parser.add_argument("-o", "--output", help="Output DOT file")
    args = parser.parse_args()

    builder = PipelineGraphBuilder(args.config)
    graph = builder.build()
    dot = graph.to_dot()
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(dot)
    else:
        print(dot)


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
