import sys
import pathlib

print("sitecustomize loaded")
path = pathlib.Path(__file__).resolve().parent / "src"
if str(path) not in sys.path:
    sys.path.insert(0, str(path))
