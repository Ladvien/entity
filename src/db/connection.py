# src/database/connection.py
"""
Centralized database connection management using dataclass
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import logging

from src.service.config import DatabaseConfig

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConnection:
    """
    Centralized database connection manager that handles all DB connections
    across the application (storage, memory, etc.)
    """

    # Connection details
    host: str
    port: int
    name: str
    username: str
    password: str
    schema: str = "public"

    # Connection options
    min_pool_size: int = 2
    max_pool_size: int = 10
    echo: bool = False

    # Internal state
    _engine: Optional[AsyncEngine] = field(default=None, init=False)
    _session_factory: Optional[sessionmaker] = field(default=None, init=False)
    _connection_url: Optional[str] = field(default=None, init=False)
    _connect_args: Dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Build connection URL and args after initialization"""
        self._build_connection_config()

    @classmethod
    def from_config(cls, config: DatabaseConfig) -> "DatabaseConnection":
        """Create DatabaseConnection from your existing config"""
        return cls(
            host=config.host,
            port=config.port,
            name=config.name,
            username=config.username,
            password=config.password,
            schema=getattr(config, "db_schema", None) or "public",
            min_pool_size=config.min_pool_size,
            max_pool_size=config.max_pool_size,
        )

    def _build_connection_config(self):
        """Build connection URL and arguments"""
        # Basic PostgreSQL+asyncpg URL
        self._connection_url = (
            f"postgresql+asyncpg://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

        # Set up connect_args for schema if not public
        if self.schema and self.schema != "public":
            self._connect_args = {"server_settings": {"search_path": self.schema}}
        else:
            self._connect_args = {}

        logger.debug(
            f"🔧 Database URL configured: {self.host}:{self.port}/{self.name} (schema: {self.schema})"
        )

    async def get_engine(self) -> AsyncEngine:
        """Get or create the SQLAlchemy engine"""
        if self._engine is None:
            self._engine = create_async_engine(
                self._connection_url,
                echo=self.echo,
                connect_args=self._connect_args,
                pool_size=self.min_pool_size,
                max_overflow=self.max_pool_size - self.min_pool_size,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,  # Recycle connections after 1 hour
            )
            logger.info(
                f"✅ Database engine created for {self.host}:{self.port}/{self.name}"
            )

        return self._engine

    async def get_session_factory(self) -> sessionmaker:
        """Get or create the session factory"""
        if self._session_factory is None:
            engine = await self.get_engine()
            self._session_factory = sessionmaker(
                engine, expire_on_commit=False, class_=AsyncSession
            )
            logger.debug("🏭 Session factory created")

        return self._session_factory

    async def get_session(self) -> AsyncSession:
        """Get a new database session"""
        factory = await self.get_session_factory()
        return factory()

    def get_sync_connection_url(self) -> str:
        """Get synchronous connection URL (for tools that need it)"""
        return (
            f"postgresql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    def get_async_connection_url(self) -> str:
        """Get asynchronous connection URL"""
        return self._connection_url

    async def test_connection(self) -> bool:
        """Test if the database connection works"""
        try:
            from sqlalchemy import text

            engine = await self.get_engine()
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False

    async def ensure_schema(self) -> bool:
        """Ensure the schema exists (create if needed)"""
        if self.schema == "public":
            return True  # Public schema always exists

        try:
            from sqlalchemy import text

            engine = await self.get_engine()
            async with engine.begin() as conn:
                await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.schema}"))
                # Set search path for this session
                await conn.execute(text(f"SET search_path TO {self.schema}"))
            logger.info(f"✅ Schema '{self.schema}' ready")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to ensure schema '{self.schema}': {e}")
            return False

    async def close(self):
        """Close all connections"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("✅ Database connections closed")

    def get_pgvector_config(self) -> Dict[str, Any]:
        """Get configuration dict for PGVector (used by memory system)"""
        return {
            "connection": self.get_async_connection_url(),
            "create_extension": False,
            "async_mode": True,
            "use_jsonb": True,
        }

    async def execute_schema_commands(self, commands: list[str]):
        """Execute multiple SQL commands in the correct schema"""
        from sqlalchemy import text

        engine = await self.get_engine()
        async with engine.begin() as conn:
            # Set search path if needed
            if self.schema != "public":
                await conn.execute(text(f"SET search_path TO {self.schema}"))

            # Execute each command separately
            for command in commands:
                await conn.execute(text(command))

    def __str__(self) -> str:
        """String representation"""
        return f"DatabaseConnection({self.host}:{self.port}/{self.name}@{self.schema})"

    def __repr__(self) -> str:
        """Detailed representation"""
        return (
            f"DatabaseConnection(host='{self.host}', port={self.port}, "
            f"name='{self.name}', schema='{self.schema}', "
            f"pool_size={self.min_pool_size}-{self.max_pool_size})"
        )


# Singleton pattern for global database connection
_global_db_connection: Optional[DatabaseConnection] = None


def get_global_db_connection() -> Optional[DatabaseConnection]:
    """Get the global database connection instance"""
    return _global_db_connection


def set_global_db_connection(db_connection: DatabaseConnection):
    """Set the global database connection instance"""
    global _global_db_connection
    _global_db_connection = db_connection
    logger.info(f"🌍 Global database connection set: {db_connection}")


async def initialize_global_db_connection(config: DatabaseConfig) -> DatabaseConnection:
    """Initialize and test the global database connection"""
    db_connection = DatabaseConnection.from_config(config)

    # Test the connection
    if not await db_connection.test_connection():
        raise ConnectionError("Failed to connect to database")

    # Ensure schema exists
    if not await db_connection.ensure_schema():
        raise RuntimeError(f"Failed to ensure schema '{db_connection.schema}'")

    # Set as global
    set_global_db_connection(db_connection)

    return db_connection
