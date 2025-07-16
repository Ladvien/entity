from __future__ import annotations

"""Simple version compatibility matrix."""

from typing import Dict, List, Set

# Map current version -> list of supported upgrade targets
COMPATIBILITY_MATRIX: Dict[str, List[str]] = {
    "0.0.1": ["0.0.1"],
}


def register_compatibility(current: str, targets: List[str]) -> None:
    """Register upgrade paths for ``current`` version."""
    COMPATIBILITY_MATRIX[current] = targets


def is_upgrade_supported(current: str, target: str) -> bool:
    """Return ``True`` if ``current`` can upgrade to ``target``.

    Performs a breadth-first search across registered upgrade paths so that
    indirect upgrades are also supported.
    """
    visited: Set[str] = set()
    queue = [current]
    while queue:
        version = queue.pop(0)
        if version == target:
            return True
        for nxt in COMPATIBILITY_MATRIX.get(version, []):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return False


__all__ = ["COMPATIBILITY_MATRIX", "register_compatibility", "is_upgrade_supported"]
