#!/usr/bin/env python
"""Detect directories that contain no files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import sys


class DirectoryScanner:
    """Scan directories recursively and report those without files."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _has_file(self, path: Path) -> bool:
        for item in path.iterdir():
            if item.is_file():
                return True
        return False

    def find_dirs_without_files(self) -> List[Path]:
        """Return directories that contain no files."""
        directories: List[Path] = []
        for p in self.root.rglob("*"):
            if not p.is_dir():
                continue
            if "\.git" in p.parts:
                continue
            if not self._has_file(p):
                directories.append(p)
        return directories


def main(argv: Iterable[str] | None = None) -> int:
    root = Path.cwd() if argv is None else Path(argv[0]).resolve()
    scanner = DirectoryScanner(root)
    empty_dirs = scanner.find_dirs_without_files()
    if empty_dirs:
        print("Directories without files detected:")
        for d in empty_dirs:
            print(d)
        return 1
    print("No directories without files detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
