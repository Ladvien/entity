import ast
import os
import sys
from typing import Set

import networkx as nx


def module_name(root: str, path: str) -> str:
    rel = os.path.relpath(path, root)
    if rel.endswith(".py"):
        rel = rel[:-3]
    return rel.replace(os.sep, ".")


def parse_imports(file_path: str) -> Set[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), file_path)
    modules: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                modules.add(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules


def build_graph(package_root: str) -> nx.DiGraph:
    graph = nx.DiGraph()
    modules: Set[str] = set()
    for dirpath, _, filenames in os.walk(package_root):
        if "templates" in dirpath:
            continue
        for f in filenames:
            if f.endswith(".py"):
                path = os.path.join(dirpath, f)
                mod = module_name(package_root, path)
                graph.add_node(mod)
                modules.add(mod)
    for mod in list(modules):
        file_path = os.path.join(package_root, mod.replace(".", os.sep) + ".py")
        if not os.path.exists(file_path):
            continue
        for target in parse_imports(file_path):
            if (
                target.startswith("pipeline")
                or target.startswith("plugins")
                or target.startswith("interfaces")
            ):
                graph.add_edge(mod, target)
    return graph


def main() -> None:
    root = os.path.join(os.path.dirname(__file__), "..", "src")
    graph = build_graph(root)
    cycles = list(nx.simple_cycles(graph))
    if cycles:
        print("Dependency cycles detected:")
        for cycle in cycles:
            print(" -> ".join(cycle))
        sys.exit(1)
    print("No dependency cycles detected")


if __name__ == "__main__":
    main()
