import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1]
if str(SRC_PATH) in sys.path:
    sys.path.remove(str(SRC_PATH))
sys.path.insert(0, str(SRC_PATH))

from .builder import ConfigBuilder  # noqa: E402
from .models import PluginConfig  # noqa: E402
from .models import PluginsSection  # noqa: E402
from .models import ServerConfig  # noqa: E402
from .models import CONFIG_SCHEMA, EntityConfig, validate_config  # noqa: E402
from .validators import _validate_memory  # noqa: E402
from .validators import _validate_cache, _validate_vector_memory  # noqa: E402

__all__ = [
    "ConfigBuilder",
    "_validate_memory",
    "_validate_vector_memory",
    "_validate_cache",
    "PluginConfig",
    "PluginsSection",
    "ServerConfig",
    "EntityConfig",
    "CONFIG_SCHEMA",
    "validate_config",
]
