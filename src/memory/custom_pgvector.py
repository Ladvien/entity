# src/memory/custom_pgvector.py - Aggressive schema-aware PGVector implementation

import logging
from typing import Optional, Any, Dict, List
from langchain_postgres.vectorstores import PGVector
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from sqlalchemy import text, MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection
import asyncio

logger = logging.getLogger(__name__)


class SchemaAwarePGVector(PGVector):
    """PGVector subclass that aggressively enforces custom schemas"""

    def __init__(
        self, embeddings: Embeddings, *, schema_name: str = "public", **kwargs
    ):
        self.schema_name = schema_name
        logger.info(f"🎯 Creating SchemaAwarePGVector for schema: {schema_name}")

        # Store original kwargs
        original_kwargs = kwargs.copy()

        # Temporarily disable auto table creation in parent
        kwargs["pre_delete_collection"] = False

        # Call parent constructor with modifications
        super().__init__(embeddings=embeddings, **kwargs)

        # Now override the collection name to include schema
        if hasattr(self, "collection_name"):
            self._original_collection_name = self.collection_name
        else:
            self._original_collection_name = "langchain"

        # Force our schema into the connection string if needed
        self._ensure_schema_in_connection()

    def _ensure_schema_in_connection(self):
        """Ensure the connection uses our schema"""
        if hasattr(self, "_connection") and self._connection:
            # Modify connection to include schema in search path
            connection_str = str(self._connection)
            if "search_path" not in connection_str and self.schema_name != "public":
                separator = "&" if "?" in connection_str else "?"
                search_path = f"options=-csearch_path%3D{self.schema_name}%2Cpublic"
                self._connection = f"{connection_str}{separator}{search_path}"
                logger.info(
                    f"🔧 Modified connection string to include schema: {self.schema_name}"
                )

    async def _get_connection(self) -> AsyncConnection:
        """Get database connection with proper schema setup"""
        if hasattr(self, "_async_engine") and self._async_engine:
            conn = await self._async_engine.connect()
        else:
            # Fall back to parent connection
            conn = await super()._get_connection()

        # Always set the search path when getting a connection
        await conn.execute(text(f'SET search_path TO "{self.schema_name}", public'))
        return conn

    async def _create_collection_if_not_exists(self) -> None:
        """Override collection creation to use correct schema"""
        logger.info(f"🔧 Creating collection in schema: {self.schema_name}")

        try:
            conn = await self._get_connection()

            # Create schema if it doesn't exist
            if self.schema_name != "public":
                await conn.execute(
                    text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"')
                )
                logger.info(f"✅ Schema '{self.schema_name}' ensured")

            # Create collection table in our schema with proper constraints
            collection_table_sql = f"""
            CREATE TABLE IF NOT EXISTS "{self.schema_name}".langchain_pg_collection (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR UNIQUE NOT NULL,
                cmetadata JSONB
            )
            """

            await conn.execute(text(collection_table_sql))
            logger.info(f"✅ Collection table created in {self.schema_name}")

            # Create embedding table in our schema
            embedding_table_sql = f"""
            CREATE TABLE IF NOT EXISTS "{self.schema_name}".langchain_pg_embedding (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                collection_id UUID REFERENCES "{self.schema_name}".langchain_pg_collection(uuid),
                embedding VECTOR,
                document TEXT,
                cmetadata JSONB,
                custom_id VARCHAR
            )
            """

            await conn.execute(text(embedding_table_sql))
            logger.info(f"✅ Embedding table created in {self.schema_name}")

            # Create the collection record - now the UNIQUE constraint exists
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

    def _make_session(self):
        """Override session creation to use schema-aware queries"""
        session = super()._make_session()

        # Set search path for this session
        if self.schema_name != "public":
            session.execute(text(f'SET search_path TO "{self.schema_name}", public'))

        return session

    async def _aensure_collection(self) -> None:
        """Async version of collection ensuring"""
        await self._create_collection_if_not_exists()

    def _get_embedding_collection_uuid(self) -> str:
        """Get collection UUID from our schema"""
        try:
            conn = self._make_session()

            # Query from our specific schema
            query = text(
                f"""
            SELECT uuid FROM "{self.schema_name}".langchain_pg_collection 
            WHERE name = :collection_name
            """
            )

            result = conn.execute(
                query, {"collection_name": self._original_collection_name}
            )
            row = result.fetchone()

            if row:
                return str(row[0])
            else:
                raise ValueError(
                    f"Collection '{self._original_collection_name}' not found in schema '{self.schema_name}'"
                )

        except Exception as e:
            logger.error(f"❌ Failed to get collection UUID: {e}")
            raise

    async def _verify_schema_setup(self) -> bool:
        """Verify that tables exist in the correct schema"""
        logger.info("🔍 Verifying schema setup...")

        try:
            conn = await self._get_connection()

            # Check if tables exist in our schema
            check_query = text(
                """
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE tablename IN ('langchain_pg_collection', 'langchain_pg_embedding')
            ORDER BY schemaname, tablename
            """
            )

            result = await conn.execute(check_query)
            tables = result.fetchall()

            logger.info("📍 Found vector tables:")
            correct_schema_count = 0

            for schema, table in tables:
                if schema == self.schema_name:
                    logger.info(f"   ✅ CORRECT: {schema}.{table}")
                    correct_schema_count += 1
                else:
                    logger.warning(f"   ❌ WRONG: {schema}.{table}")

            await conn.close()

            success = correct_schema_count >= 2
            if success:
                logger.info(
                    f"✅ SUCCESS: Vector tables verified in '{self.schema_name}' schema"
                )
            else:
                logger.error(
                    f"💥 FAILURE: Vector tables not properly set up in '{self.schema_name}' schema"
                )

            return success

        except Exception as e:
            logger.error(f"❌ Failed to verify schema setup: {e}")
            return False

    @classmethod
    async def afrom_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        collection_name: str = "langchain",
        schema_name: str = "public",
        **kwargs,
    ) -> "SchemaAwarePGVector":
        """Async factory method with proper schema handling"""
        logger.info(
            f"🚀 Creating SchemaAwarePGVector from texts in schema: {schema_name}"
        )

        # Create instance
        instance = cls(
            embeddings=embedding,
            collection_name=collection_name,
            schema_name=schema_name,
            **kwargs,
        )

        # Set up schema and tables
        await instance._create_collection_if_not_exists()

        # Verify setup
        await instance._verify_schema_setup()

        # Add texts if provided
        if texts:
            documents = [
                Document(page_content=text, metadata=metadatas[i] if metadatas else {})
                for i, text in enumerate(texts)
            ]
            await instance.aadd_documents(documents)

        return instance

    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        collection_name: str = "langchain",
        schema_name: str = "public",
        **kwargs,
    ) -> "SchemaAwarePGVector":
        """Sync factory method - runs async version"""
        logger.info(
            f"🚀 Creating SchemaAwarePGVector from texts (sync) in schema: {schema_name}"
        )

        # Run the async version
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(
                cls.afrom_texts(
                    texts=texts,
                    embedding=embedding,
                    metadatas=metadatas,
                    collection_name=collection_name,
                    schema_name=schema_name,
                    **kwargs,
                )
            )
        finally:
            if loop.is_running():
                pass  # Don't close a running loop
            else:
                loop.close()
