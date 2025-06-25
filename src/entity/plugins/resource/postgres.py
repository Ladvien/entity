# src/entity/plugins/resource/postgres.py
import asyncpg
from .base import ResourcePlugin


class PostgresResourcePlugin(ResourcePlugin):
    def get_resource_name(self) -> str:
        return "data"

    async def initialize(self, config: dict):
        return await asyncpg.create_pool(
            user=config["username"],
            password=config["password"],
            database=config["name"],
            host=config["host"],
            port=config.get("port", 5432),
            min_size=config.get("min_pool_size", 2),
            max_size=config.get("max_pool_size", 10),
        )
