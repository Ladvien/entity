import re
from pathlib import Path


def test_user_plugins_do_not_import_pipeline():
    base = Path("user_plugins")
    pattern = re.compile(r"^(?:from|import)\s+(entity\.pipeline|pipeline)")
    offending = []
    for py_file in base.rglob("*.py"):
        with py_file.open() as f:
            for lineno, line in enumerate(f, 1):
                if pattern.search(line):
                    offending.append(f"{py_file}:{lineno}:{line.strip()}")
    assert not offending, "Forbidden pipeline imports found:\n" + "\n".join(offending)
