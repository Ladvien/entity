from __future__ import annotations

import argparse
from textwrap import indent

from entity.workflow.workflow import Workflow
from entity.workflow.executor import WorkflowExecutor


def ascii_diagram(workflow: Workflow) -> str:
    lines = []
    for stage in WorkflowExecutor._ORDER:
        lines.append(stage)
        for plugin in workflow.plugins_for(stage):
            lines.append(indent(f"- {plugin.__name__}", "  "))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize a workflow")
    parser.add_argument("file", help="YAML workflow definition")
    args = parser.parse_args()

    wf = Workflow.from_yaml(args.file)
    print(ascii_diagram(wf))


if __name__ == "__main__":  # pragma: no cover
    main()
