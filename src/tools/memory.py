# src/tools/memory.py - FIXED VERSION

from typing import List, Optional, Dict, Any
import logging

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_postgres.vectorstores import PGVector

from sqlalchemy import text
from pydantic import BaseModel

from src.service.config import DatabaseConfig, MemoryConfig
from src.db.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class MemorySearchInput(BaseModel):
    query: str
    thread_id: str


class VectorMemorySystem:
    """
    Vector memory system using LangChain's PGVector with centralized database connection.
    Stores conversational and observational memory with metadata.
    """

    def __init__(self, memory_config: MemoryConfig, database_config: DatabaseConfig):
        self.memory_config = memory_config
        self.database_config = database_config

        # Create centralized database connection
        self.db_connection = DatabaseConnection.from_config(database_config)

        self.collection_name = memory_config.collection_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=memory_config.embedding_model
        )
        self.sentence_model = SentenceTransformer(memory_config.embedding_model)
        self.vector_store = None

    async def initialize(self):
        """Initialize the vector store using centralized connection"""
        try:
            # Debug: Check what methods are available on db_connection
            logger.debug(f"DatabaseConnection type: {type(self.db_connection)}")
            logger.debug(
                f"DatabaseConnection methods: {[m for m in dir(self.db_connection) if not m.startswith('_')]}"
            )

            # Test and ensure schema using centralized connection
            if not await self.db_connection.test_connection():
                raise ConnectionError("Failed to connect to database for vector memory")

            if not await self.db_connection.ensure_schema():
                raise RuntimeError(
                    f"Failed to ensure schema '{self.db_connection.schema}' for vector memory"
                )

            # Use the centralized connection URL for PGVector
            # Build the connection URL from the DatabaseConnection properties
            if hasattr(self.db_connection, "get_async_connection_url"):
                conn_url = self.db_connection.get_async_connection_url()
                logger.debug("Using get_async_connection_url() method")
            elif hasattr(self.db_connection, "_connection_url"):
                conn_url = self.db_connection._connection_url
                logger.debug("Using _connection_url property")
            else:
                # Fallback: construct the URL manually
                conn_url = (
                    f"postgresql+asyncpg://{self.db_connection.username}:{self.db_connection.password}"
                    f"@{self.db_connection.host}:{self.db_connection.port}/{self.db_connection.name}"
                )
                logger.debug("Using manual URL construction")

            logger.debug(
                f"Vector store connection URL: {conn_url.replace(self.db_connection.password, '***')}"
            )

            self.vector_store = PGVector(
                embeddings=self.embeddings,
                connection=conn_url,
                collection_name=self.collection_name,
                create_extension=False,
                async_mode=True,
                use_jsonb=True,
            )

            # Force creation of vector tables by adding a dummy document and removing it
            try:
                await self._ensure_vector_tables_exist()
                logger.info("✅ Vector memory tables initialized")
            except Exception as e:
                logger.warning(
                    f"⚠️ Could not pre-create vector tables (they'll be created on first use): {e}"
                )

            logger.info(
                f"✅ PGVector memory initialized with centralized connection (schema: {self.db_connection.schema})"
            )

        except Exception as e:
            logger.error(f"❌ Failed to initialize vector memory: {e}")
            raise

    async def _ensure_vector_tables_exist(self):
        """Ensure vector tables exist by adding and removing a dummy document"""
        try:
            dummy_doc = Document(
                page_content="__INIT_DUMMY__",
                metadata={"__init": True, "thread_id": "__init__"},
            )

            # Add dummy document to force table creation
            await self.vector_store.aadd_documents([dummy_doc])

            # Remove the dummy document
            # Note: This is a bit hacky but ensures tables exist
            session = await self.db_connection.get_session()
            async with session:
                await session.execute(
                    text(
                        """
                        DELETE FROM langchain_pg_embedding 
                        WHERE collection_id = CAST(
                            (SELECT id FROM langchain_pg_collection WHERE name = :name) 
                            AS UUID
                        ) AND cmetadata->>'__init' = 'true'
                        """
                    ),
                    {"name": self.collection_name},
                )
                await session.commit()

            logger.debug("🔧 Vector tables created and dummy data cleaned up")

        except Exception as e:
            logger.debug(f"Could not pre-initialize vector tables: {e}")
            # This is not critical - tables will be created on first real use

    async def add_memory(
        self,
        thread_id: str,
        content: str,
        memory_type: str = "observation",
        importance_score: float = 0.5,
        emotional_tone: str = "neutral",
        topics: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a memory entry"""
        try:
            doc = Document(
                page_content=content,
                metadata={
                    "thread_id": thread_id,
                    "memory_type": memory_type,
                    "importance_score": importance_score,
                    "emotional_tone": emotional_tone,
                    "topics": topics or [],
                    **(metadata or {}),
                },
            )
            await self.vector_store.aadd_documents([doc])
            logger.info("📝 Memory added to PGVector")
        except Exception as e:
            logger.exception("❌ Failed to add memory")
            raise

    # Replace the search_memory method in src/tools/memory.py

    async def search_memory(
        self, query: str, thread_id: Optional[str] = None, k: int = 5
    ) -> List[Document]:
        """Search memories"""
        try:
            # Simple approach - don't use thread filtering for now since it's causing issues
            # Just search all memories and filter afterwards if needed
            results = await self.vector_store.asimilarity_search(query, k=k)

            # If thread_id specified, filter results manually
            if thread_id:
                filtered_results = []
                for doc in results:
                    if doc.metadata.get("thread_id") == thread_id:
                        filtered_results.append(doc)
                results = filtered_results[:k]  # Limit to k results

            logger.info(f"🔍 Retrieved {len(results)} memory entries")
            return results
        except Exception as e:
            logger.exception("❌ Memory search failed")
            logger.error(f"Memory search error: {e}")
            return []

    async def get_memory_context(
        self, query: str, thread_id: str = "default", k: int = 5
    ) -> str:
        """Get formatted memory context"""
        try:
            memories = await self.search_memory(query=query, thread_id=thread_id, k=k)
            if not memories:
                return ""

            context_parts = []
            for doc in memories:
                # Extract key info from metadata
                memory_type = doc.metadata.get("memory_type", "unknown")
                importance = doc.metadata.get("importance_score", 0.5)

                if importance > 0.7:
                    context_parts.append(f"[Important] {doc.page_content}")
                else:
                    context_parts.append(f"[{memory_type}] {doc.page_content}")

            return "\n".join(context_parts)
        except Exception as e:
            logger.exception("❌ Failed to retrieve memory context")
            return ""

    async def store_conversation(
        self, user_input: str, ai_response: str, thread_id: str = "default"
    ):
        """Store a conversation exchange"""
        try:
            combined_text = f"User: {user_input}\nAssistant: {ai_response}"
            await self.add_memory(
                thread_id=thread_id,
                content=combined_text,
                memory_type="conversation",
                importance_score=0.5,
                emotional_tone="neutral",
            )
            logger.info("💾 Conversation stored in vector memory")
        except Exception as e:
            logger.exception("❌ Failed to store conversation")

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics using centralized connection"""
        stats = {
            "total_memories": 0,
            "total_conversations": 0,
            "memory_types": {},
            "emotions": {},
            "top_topics": {},
            "backend": "pgvector",
            "vector_dimensions": self.memory_config.embedding_dimension,
            "embedding_model": self.memory_config.embedding_model,
            "status": "not_initialized",
        }

        try:
            # Use centralized connection for stats queries
            session = await self.db_connection.get_session()
            async with session:
                # First check if the vector tables exist using information_schema
                # This won't fail even if the tables don't exist
                try:
                    tables_check_result = await session.execute(
                        text(
                            """
                            SELECT 
                                COUNT(*) FILTER (WHERE table_name = 'langchain_pg_embedding') as embedding_table_exists,
                                COUNT(*) FILTER (WHERE table_name = 'langchain_pg_collection') as collection_table_exists
                            FROM information_schema.tables 
                            WHERE table_schema = CURRENT_SCHEMA()
                            AND table_name IN ('langchain_pg_embedding', 'langchain_pg_collection')
                            """
                        )
                    )

                    table_counts = tables_check_result.fetchone()
                    embedding_exists = table_counts[0] > 0
                    collection_exists = table_counts[1] > 0

                    if not (embedding_exists and collection_exists):
                        stats["status"] = "tables_not_created"
                        stats["tables_status"] = {
                            "langchain_pg_embedding": embedding_exists,
                            "langchain_pg_collection": collection_exists,
                        }
                        logger.info(
                            "📊 Vector memory tables not yet created - stats will be empty until first memory is stored"
                        )
                        return stats

                except Exception as schema_error:
                    logger.warning(f"Could not check table existence: {schema_error}")
                    stats["status"] = "schema_check_failed"
                    stats["error"] = str(schema_error)
                    return stats

                # Now safely check if our specific collection exists
                try:
                    collection_exists_result = await session.execute(
                        text(
                            """
                            SELECT EXISTS (
                                SELECT 1 FROM langchain_pg_collection 
                                WHERE name = :name
                            )
                            """
                        ),
                        {"name": self.collection_name},
                    )

                    collection_exists = collection_exists_result.scalar_one()

                    if not collection_exists:
                        stats["status"] = "collection_not_created"
                        logger.info(
                            f"📊 Collection '{self.collection_name}' not yet created - stats will be empty until first memory is stored"
                        )
                        return stats

                except Exception as collection_error:
                    logger.warning(
                        f"Could not check collection existence: {collection_error}"
                    )
                    stats["status"] = "collection_check_failed"
                    stats["error"] = str(collection_error)
                    return stats

                # Now we can safely get stats
                stats["status"] = "active"

                try:
                    # Get total count
                    result = await session.execute(
                        text(
                            """
                            SELECT COUNT(*) 
                            FROM langchain_pg_embedding 
                            WHERE collection_id = CAST(
                                (SELECT id FROM langchain_pg_collection WHERE name = :name) 
                                AS UUID
                            )
                            """
                        ),
                        {"name": self.collection_name},
                    )

                    stats["total_memories"] = result.scalar_one()

                    # Get metadata stats
                    result = await session.execute(
                        text(
                            """
                            SELECT cmetadata 
                            FROM langchain_pg_embedding 
                            WHERE collection_id = CAST(
                                (SELECT id FROM langchain_pg_collection WHERE name = :name)
                                AS UUID
                            )
                            LIMIT 1000
                            """
                        ),
                        {"name": self.collection_name},
                    )

                    rows = result.fetchall()

                    thread_ids = set()
                    memory_types = {}
                    emotions = {}
                    topics = {}

                    for row in rows:
                        meta = row[0] or {}
                        thread_ids.add(meta.get("thread_id", "default"))

                        mt = meta.get("memory_type", "observation")
                        memory_types[mt] = memory_types.get(mt, 0) + 1

                        tone = meta.get("emotional_tone", "neutral")
                        emotions[tone] = emotions.get(tone, 0) + 1

                        for topic in meta.get("topics", []):
                            topics[topic] = topics.get(topic, 0) + 1

                    stats["total_conversations"] = len(thread_ids)
                    stats["memory_types"] = memory_types
                    stats["emotions"] = emotions
                    stats["top_topics"] = dict(
                        sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]
                    )

                    logger.info(
                        f"📊 Memory stats retrieved: {stats['total_memories']} memories, {stats['total_conversations']} conversations"
                    )

                except Exception as stats_error:
                    logger.warning(f"Could not retrieve detailed stats: {stats_error}")
                    stats["status"] = "partial_failure"
                    stats["error"] = str(stats_error)

        except Exception as e:
            logger.exception("❌ Failed to get memory stats")
            stats["status"] = "error"
            stats["error"] = str(e)

        return stats

    async def close(self):
        """Close connections using centralized connection"""
        await self.db_connection.close()
        logger.info("✅ Memory system closed")
