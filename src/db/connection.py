from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import text
import logging
import asyncio
from sqlalchemy import create_engine
from src.core.config import DataConfig

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

    _engine: Optional[AsyncEngine] = None

    @property
    def async_engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(
                self.async_connection_url,
                echo=self.echo,
                connect_args=self.connect_args,
                pool_size=self.min_pool_size,
                max_overflow=max(0, self.max_pool_size - self.min_pool_size),
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            logger.info(f"✅ Created async engine for {self}")
        return self._engine

    def get_pgvector_config(self) -> Dict[str, Any]:
        return {
            "connection": self.async_engine,
            "async_mode": True,
            "create_extension": False,
            "use_jsonb": True,
            "pre_delete_collection": False,
            "collection_name": self.schema,  # Use schema as collection name
        }

    @classmethod
    def from_config(cls, config: DataConfig) -> "DatabaseConnection":
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
    def connect_args(self) -> Dict[str, Any]:
        return (
            {"server_settings": {"search_path": f"{self.schema},public"}}
            if self.schema != "public"
            else {}
        )

    def create_sync_engine(self):
        """
        Create a synchronous SQLAlchemy engine for DDL operations.
        """
        # Construct sync DB URL by replacing async driver with sync driver
        # Example: postgresql+asyncpg://user:pass@host:port/db -> postgresql+psycopg://user:pass@host:port/db

        # Assuming you have something like this stored in your config:
        user = self.username
        password = self.password
        host = self.host
        port = self.port
        dbname = self.name

        # Use psycopg (v3) sync driver recommended:
        sync_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"

        # Create and return sync engine
        return create_engine(sync_url)

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

    def async_session(self) -> async_sessionmaker[AsyncSession]:
        if not self._engine:
            raise RuntimeError(
                "Engine not initialized. Call `await get_engine()` first."
            )
        return async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    async def get_session(self) -> AsyncSession:
        session = self.async_session()()

        # Always force search path on every session to ensure schema priority
        if self.schema != "public":
            try:
                await session.execute(text(f"SET search_path TO {self.schema}, public"))
                logger.debug(f"🔧 Set search_path to: {self.schema}, public")
            except Exception as e:
                logger.warning(f"⚠️ Failed to set search_path: {e}")

        return session

    async def test_connection(self) -> bool:
        try:
            engine = await self.get_engine()
            async with engine.begin() as conn:
                if self.schema != "public":
                    await conn.execute(
                        text(f"SET search_path TO {self.schema}, public")
                    )
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
                await conn.execute(text(f"SET search_path TO {self.schema}, public"))
            logger.info(f"✅ Schema '{self.schema}' ready")
            return True
        except Exception as e:
            logger.error(f"❌ Could not ensure schema '{self.schema}': {e}")
            return False

    async def execute_schema_commands(self, commands: List[str]):
        engine = await self.get_engine()
        async with engine.begin() as conn:
            if self.schema != "public":
                await conn.execute(text(f"SET search_path TO {self.schema}, public"))
            for command in commands:
                await conn.execute(text(command))

    async def close(self):
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            logger.info("✅ Engine closed and reset")

    def __str__(self):
        return f"{self.username}@{self.host}:{self.port}/{self.name} (schema={self.schema})"

    def __repr__(self):
        return (
            f"DatabaseConnection(host='{self.host}', port={self.port}, name='{self.name}', "
            f"schema='{self.schema}', pool={self.min_pool_size}-{self.max_pool_size})"
        )


# --- Global DB connection registry ---
_global_db_connection: Optional[DatabaseConnection] = None


def get_global_db_connection() -> Optional[DatabaseConnection]:
    return _global_db_connection


def set_global_db_connection(db_connection: DatabaseConnection):
    global _global_db_connection
    _global_db_connection = db_connection
    logger.info(f"🌍 Global DB connection set: {db_connection}")


async def initialize_global_db_connection(config: DataConfig) -> DatabaseConnection:
    db_connection = DatabaseConnection.from_config(config)

    if not await db_connection.test_connection():
        raise ConnectionError("Failed to connect to database")

    if not await db_connection.ensure_schema():
        raise RuntimeError(f"Schema creation failed for: {db_connection.schema}")

    set_global_db_connection(db_connection)
    return db_connection


_global_async_engine: AsyncEngine = None


def get_global_async_engine() -> AsyncEngine:
    return _global_async_engine


def set_global_async_engine(engine: AsyncEngine):
    global _global_async_engine
    _global_async_engine = engine


async def close_global_db_connection():
    db = get_global_db_connection()
    if db is not None:
        await db.close()
