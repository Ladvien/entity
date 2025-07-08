#!/usr/bin/env python
"""Detect directories that contain no files at any depth."""

from __future__ import annotations

import sys
from pathlib import Path


class EmptyDirectoryChecker:
    """Detect directories within the repository that contain no files or subdirectories."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _contains_file(self, path: Path) -> bool:
        """Return ``True`` if ``path`` or any descendant directory contains a file."""
        return any(p.is_file() for p in path.rglob("*"))

    def find_dirs_without_files(self) -> List[Path]:
        """Return directories that contain no files."""
        directories: List[Path] = []
        for p in self.root.rglob("*"):
            if not p.is_dir():
                continue
            if ".git" in p.parts:
                continue
            if not self._contains_file(p):
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
