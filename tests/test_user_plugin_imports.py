import re
from pathlib import Path


<<<<<<< HEAD
def test_user_plugins_do_not_import_pipeline():
=======
def test_plugin_library_does_not_import_pipeline():
>>>>>>> pr-1829
    base = Path("plugin_library")
    pattern = re.compile(r"^(?:from|import)\s+(entity\.pipeline|pipeline)")
    offending = []
    for py_file in base.rglob("*.py"):
        with py_file.open() as f:
            for lineno, line in enumerate(f, 1):
                if pattern.search(line):
                    offending.append(f"{py_file}:{lineno}:{line.strip()}")
    assert not offending, "Forbidden pipeline imports found:\n" + "\n".join(offending)
