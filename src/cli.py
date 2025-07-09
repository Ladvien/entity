"""Deprecated CLI wrapper. Use :mod:`entity.cli` instead."""

from __future__ import annotations

from entity.cli import main

if __name__ == "__main__":  # pragma: no cover - wrapper
    main()
