import asyncio
import logging
from logging.handlers import RotatingFileHandler

from pipeline.plugins.resources.structured_logging import StructuredLogging


async def init_logging(cfg):
    plugin = StructuredLogging(cfg)
    await plugin.initialize()


def test_structured_logging_initializes(tmp_path):
    config = {
        "level": "WARNING",
        "format": "%(levelname)s:%(message)s",
        "file_enabled": True,
        "file_path": str(tmp_path / "entity.log"),
        "max_file_size": 1024,
        "backup_count": 1,
    }
    asyncio.run(init_logging(config))

    root_logger = logging.getLogger()
    assert root_logger.level == logging.WARNING
    assert any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers)
    assert any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)
