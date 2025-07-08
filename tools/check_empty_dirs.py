from __future__ import annotations

import sys
from pathlib import Path


class EmptyDirectoryChecker:
    """Detect directories within the repository that contain no files or subdirectories."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def find(self) -> list[Path]:
        """Return a list of empty directories under the repository root."""
        empty_dirs: list[Path] = []
        for path in self.root.rglob("*"):
            if ".git" in path.parts or not path.is_dir():
                continue
            if not any(path.iterdir()):
                empty_dirs.append(path)
        return empty_dirs

    def run(self) -> int:
        """Print any empty directories found and return an exit code."""
        empty = self.find()
        if empty:
            print("Empty directories found:")
            for directory in empty:
                print(directory.relative_to(self.root))
            return 1
        return 0


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    checker = EmptyDirectoryChecker(repo_root)
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())
