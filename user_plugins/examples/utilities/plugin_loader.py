"""Example showing Agent.from_directory error handling.

Run with ``python -m examples.utilities.plugin_loader`` or install the package in
editable mode.
"""

from __future__ import annotations

import pathlib

from . import enable_plugins_namespace

enable_plugins_namespace()


def main() -> None:
    """Placeholder for plugin loading demo."""

    print("Plugin loader example requires full pipeline modules")


if __name__ == "__main__":
    main()
