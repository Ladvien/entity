import logging
from typing import Optional, List, Union
from langchain_postgres.vectorstores import PGVector
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

logger = logging.getLogger(__name__)


class SchemaAwarePGVector(PGVector):
    def __init__(
        self,
        embeddings: Embeddings,
        *,
        connection: Optional[Union[str, AsyncEngine]] = None,
        schema_name: str = "entity",
        async_mode: bool = True,
        **kwargs,
    ):
        self.schema_name = schema_name
        logger.info(f"🎯 Creating SchemaAwarePGVector for schema: {schema_name}")

        if connection is None:
            raise ValueError(
                "connection must be provided as connection string or AsyncEngine"
            )

        if isinstance(connection, str):
            self._async_engine = create_async_engine(connection, future=True)
            connection_arg = self._async_engine
        elif isinstance(connection, AsyncEngine):
            self._async_engine = connection
            connection_arg = connection
        else:
            raise TypeError("connection must be str or AsyncEngine")

        logger.info(
            f"SchemaAwarePGVector.__init__: connection type: {type(connection_arg)}"
        )
        logger.debug(
            f"SchemaAwarePGVector.__init__: connection value: {connection_arg}"
        )

        kwargs["pre_delete_collection"] = False
        kwargs["create_extension"] = False

        super().__init__(embeddings=embeddings, connection=connection_arg, **kwargs)

        self._original_collection_name = getattr(self, "collection_name", "langchain")

    async def _get_connection(self) -> AsyncConnection:
        if hasattr(self, "_async_engine") and self._async_engine:
            conn = await self._async_engine.connect()
        else:
            raise RuntimeError("No async engine available; cannot get async connection")

        await conn.execute(text(f'SET search_path TO "{self.schema_name}", public'))
        return conn

    async def _create_collection_if_not_exists(self) -> None:
        logger.info(f"🔧 Creating collection in schema: {self.schema_name}")

        try:
            conn = await self._get_connection()

            if self.schema_name != "public":
                await conn.execute(
                    text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"')
                )
                logger.info(f"✅ Schema '{self.schema_name}' ensured")

            collection_table_sql = f"""
            CREATE TABLE IF NOT EXISTS "{self.schema_name}".langchain_pg_collection (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR UNIQUE NOT NULL,
                cmetadata JSONB
            )
            """
            await conn.execute(text(collection_table_sql))

            embedding_table_sql = f"""
            CREATE TABLE IF NOT EXISTS "{self.schema_name}".langchain_pg_embedding (
                id VARCHAR PRIMARY KEY,
                collection_id UUID REFERENCES "{self.schema_name}".langchain_pg_collection(uuid),
                embedding VECTOR,
                document TEXT,
                cmetadata JSONB,
                custom_id VARCHAR
            )
            """
            await conn.execute(text(embedding_table_sql))

            collection_insert_sql = f"""
            INSERT INTO "{self.schema_name}".langchain_pg_collection (name, cmetadata)
            VALUES (:collection_name, :metadata)
            ON CONFLICT (name) DO NOTHING
            """
            await conn.execute(
                text(collection_insert_sql),
                {"collection_name": self._original_collection_name, "metadata": "{}"},
            )

            await conn.commit()
            await conn.close()

            logger.info(
                f"✅ Collection '{self._original_collection_name}' ready in {self.schema_name}"
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to create collection in schema {self.schema_name}: {e}"
            )
            raise

    @classmethod
    async def afrom_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        collection_name: str = "langchain",
        schema_name: str = "entity",
        connection: Optional[Union[str, AsyncEngine]] = None,
        **kwargs,
    ) -> "SchemaAwarePGVector":
        if connection is None:
            raise RuntimeError("Connection string or AsyncEngine must be provided")

        instance = cls(
            embeddings=embedding,
            collection_name=collection_name,
            schema_name=schema_name,
            connection=connection,
            **kwargs,
        )

        await instance._create_collection_if_not_exists()
        await instance._verify_schema_setup()

        if texts:
            documents = [Document(page_content=text, metadata={}) for text in texts]
            await instance.aadd_documents(documents)

        return instance

    async def _verify_schema_setup(self) -> None:
        conn = await self._get_connection()
        await conn.execute(
            text(
                """
                SELECT 1
                FROM pg_tables
                WHERE schemaname = :schema
                  AND tablename IN ('langchain_pg_collection',
                                    'langchain_pg_embedding')
                LIMIT 1
            """
            ),
            {"schema": self.schema_name},
        )
        await conn.close()


class SchemaAwarePGVectorNoDDL(SchemaAwarePGVector):
    def create_tables_if_not_exists(self):
        pass

    def create_collection(self):
        pass

    async def _verify_schema_setup(self):
        logger.info("🧪 Skipping schema verification (NoDDL mode)")
