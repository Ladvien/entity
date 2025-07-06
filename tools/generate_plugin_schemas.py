import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from plugins.builtin.config_models import PLUGIN_CONFIG_MODELS

SCHEMA_DIR = Path("docs/source/schemas")
SCHEMA_DIR.mkdir(exist_ok=True)

for name, model in PLUGIN_CONFIG_MODELS.items():
    schema_path = SCHEMA_DIR / f"{name}.json"
    schema_path.write_text(json.dumps(model.schema(), indent=2))

print(f"Wrote {len(PLUGIN_CONFIG_MODELS)} schemas to {SCHEMA_DIR}")
