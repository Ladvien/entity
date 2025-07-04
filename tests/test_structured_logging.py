import asyncio
import json
import logging
import os
from logging.handlers import RotatingFileHandler

from plugins.resources.structured_logging import StructuredLogging


async def init_logging(cfg):
    plugin = StructuredLogging(cfg)
    await plugin.initialize()


def test_structured_logging_initializes(tmp_path):
    path = tmp_path / "entity.log"
    os.environ["ENTITY_LOG_PATH"] = str(path)
    config = {
        "level": "WARNING",
        "file_enabled": True,
        "max_file_size": 1024,
        "backup_count": 1,
    }

    asyncio.run(init_logging(config))

    root_logger = logging.getLogger()
    assert root_logger.level == logging.WARNING
    assert any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers)
    assert any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)
    root_logger.warning("test")
    for handler in root_logger.handlers:
        handler.flush()

    with open(path) as fh:
        line = fh.readline()
        data = json.loads(line)
    assert data["level"] == "WARNING"
    assert data["message"]

    del os.environ["ENTITY_LOG_PATH"]
