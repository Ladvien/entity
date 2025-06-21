"""
Centralized database connection management using dataclass
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import logging

from src.service.config import DatabaseConfig

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConnection:
    host: str
    port: int
    name: str
    username: str
    password: str
    schema: str = "public"

    min_pool_size: int = 2
    max_pool_size: int = 10
    echo: bool = False

    _engine: Optional[AsyncEngine] = field(default=None, init=False)
    _session_factory: Optional[sessionmaker] = field(default=None, init=False)
    _async_session_maker: Optional[async_sessionmaker[AsyncSession]] = field(
        default=None, init=False
    )

    @classmethod
    def from_config(cls, config: DatabaseConfig) -> "DatabaseConnection":
        return cls(
            host=config.host,
            port=config.port,
            name=config.name,
            username=config.username,
            password=config.password,
            schema=getattr(config, "db_schema", "public"),
            min_pool_size=config.min_pool_size,
            max_pool_size=config.max_pool_size,
        )

    @property
    def async_connection_url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_connection_url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def connect_args(self) -> Dict[str, Any]:
        if self.schema and self.schema != "public":
            return {"server_settings": {"search_path": self.schema}}
        return {}

    async def get_engine(self) -> AsyncEngine:
        if not self._engine:
            self._engine = create_async_engine(
                self.async_connection_url,
                echo=self.echo,
                connect_args=self.connect_args,
                pool_size=self.min_pool_size,
                max_overflow=self.max_pool_size - self.min_pool_size,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            logger.info(f"✅ Created engine for {self}")
        return self._engine

    async def get_session_factory(self) -> sessionmaker:
        if not self._session_factory:
            engine = await self.get_engine()
            self._session_factory = sessionmaker(
                engine, expire_on_commit=False, class_=AsyncSession
            )
            logger.debug("🏭 Session factory initialized")
        return self._session_factory

    async def get_session(self) -> AsyncSession:
        factory = await self.get_session_factory()
        return factory()

    async def test_connection(self) -> bool:
        try:
            engine = await self.get_engine()
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection test passed")
            return True
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    async def ensure_schema(self) -> bool:
        if self.schema == "public":
            return True
        try:
            engine = await self.get_engine()
            async with engine.begin() as conn:
                await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.schema}"))
                await conn.execute(text(f"SET search_path TO {self.schema}"))
            logger.info(f"✅ Schema '{self.schema}' ready")
            return True
        except Exception as e:
            logger.error(f"❌ Could not ensure schema '{self.schema}': {e}")
            return False

    async def execute_schema_commands(self, commands: List[str]):
        engine = await self.get_engine()
        async with engine.begin() as conn:
            if self.schema != "public":
                await conn.execute(text(f"SET search_path TO {self.schema}"))
            for command in commands:
                await conn.execute(text(command))

    def get_pgvector_config(self) -> Dict[str, Any]:
        return {
            "connection": self.async_connection_url,
            "create_extension": False,
            "async_mode": True,
            "use_jsonb": True,
        }

    async def close(self):
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("✅ Engine closed and reset")

    def async_session(self) -> async_sessionmaker[AsyncSession]:
        if not self._async_session_maker:
            self._initialize_session_factory()  # <- ensures it's ready
        return self._async_session_maker

    def __str__(self):
        return f"{self.username}@{self.host}:{self.port}/{self.name} (schema={self.schema})"

    def __repr__(self):
        return (
            f"DatabaseConnection(host='{self.host}', port={self.port}, name='{self.name}', "
            f"schema='{self.schema}', pool={self.min_pool_size}-{self.max_pool_size})"
        )

    def _initialize_session_factory(self):
        if not self._engine:
            raise RuntimeError("Database engine is not initialized")
        self._async_session_maker = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )
        logger.debug(
            "🏭 async_sessionmaker initialized via _initialize_session_factory()"
        )


# Global connection instance
_global_db_connection: Optional[DatabaseConnection] = None


def get_global_db_connection() -> Optional[DatabaseConnection]:
    return _global_db_connection


def set_global_db_connection(db_connection: DatabaseConnection):
    global _global_db_connection
    _global_db_connection = db_connection
    logger.info(f"🌍 Global DB connection set: {db_connection}")


async def initialize_global_db_connection(config: DatabaseConfig) -> DatabaseConnection:
    db_connection = DatabaseConnection.from_config(config)

    if not await db_connection.test_connection():
        raise ConnectionError("Failed to connect to database")

    if not await db_connection.ensure_schema():
        raise RuntimeError(f"Schema creation failed for: {db_connection.schema}")

    set_global_db_connection(db_connection)
    return db_connection
