from __future__ import annotations

"""Simple version compatibility matrix."""

from typing import Dict, List

# Map current version -> list of supported upgrade targets
COMPATIBILITY_MATRIX: Dict[str, List[str]] = {
    "0.0.1": ["0.0.1"],
}


def register_compatibility(current: str, targets: List[str]) -> None:
    """Register upgrade paths for ``current`` version."""
    COMPATIBILITY_MATRIX[current] = targets


def is_upgrade_supported(current: str, target: str) -> bool:
    """Return ``True`` if ``current`` can upgrade to ``target``."""
    return target in COMPATIBILITY_MATRIX.get(current, [])


__all__ = ["COMPATIBILITY_MATRIX", "register_compatibility", "is_upgrade_supported"]
