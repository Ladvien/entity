# entity/memory.py - Updated with PostgreSQL fallback (no vector extension needed)

import asyncio
import logging
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import asyncpg

logger = logging.getLogger(__name__)


class VectorMemorySystem:
    """PostgreSQL memory system with text search fallback when pgvector not available"""

    def __init__(self, settings=None):
        self.settings = settings
        self.pool = None
        self.embedding_model = None
        self.embedding_dim = 384
        self.initialized = False
        self.use_vector_search = False

        # Initialize embedding model
        try:
            from sentence_transformers import SentenceTransformer

            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✅ Sentence transformer model loaded")
            self.use_embeddings = True
        except ImportError:
            logger.warning(
                "⚠️  sentence-transformers not available, using text search only"
            )
            self.embedding_model = None
            self.use_embeddings = False

    async def initialize(self):
        """Initialize database connection and create tables"""
        if self.initialized:
            return

        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=self.settings.database.host,
                port=self.settings.database.port,
                database=self.settings.database.name,
                user=self.settings.database.username,
                password=self.settings.database.password,
                min_size=2,
                max_size=10,
            )

            # Create tables (with or without vector support)
            await self._create_tables()

            logger.info("✅ PostgreSQL memory system initialized")
            self.initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL memory: {e}")
            raise

    async def _create_tables(self):
        """Create necessary database tables with fallback for no vector extension"""
        async with self.pool.acquire() as conn:
            # Try to enable pgvector extension
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self.use_vector_search = True
                logger.info("✅ pgvector extension available")
            except Exception as e:
                logger.warning(f"Could not create vector extension: {e}")
                self.use_vector_search = False
                logger.info("📝 Using text search instead of vector search")

            # Conversations table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    thread_id VARCHAR(255) NOT NULL,
                    user_input TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb
                );
            """
            )

            # Memory entries table - conditional vector column
            if self.use_vector_search:
                # With vector support
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS memory_entries (
                        id SERIAL PRIMARY KEY,
                        thread_id VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        content_hash VARCHAR(64) UNIQUE NOT NULL,
                        embedding vector({self.embedding_dim}),
                        memory_type VARCHAR(50) NOT NULL,
                        importance_score FLOAT DEFAULT 0.5,
                        emotional_tone VARCHAR(50) DEFAULT 'neutral',
                        topics TEXT[] DEFAULT ARRAY[]::TEXT[],
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        access_count INTEGER DEFAULT 1,
                        metadata JSONB DEFAULT '{{}}'::jsonb
                    );
                """
                )
            else:
                # Without vector support - use JSONB for embedding storage
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_entries (
                        id SERIAL PRIMARY KEY,
                        thread_id VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        content_hash VARCHAR(64) UNIQUE NOT NULL,
                        embedding_json JSONB,
                        memory_type VARCHAR(50) NOT NULL,
                        importance_score FLOAT DEFAULT 0.5,
                        emotional_tone VARCHAR(50) DEFAULT 'neutral',
                        topics TEXT[] DEFAULT ARRAY[]::TEXT[],
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        access_count INTEGER DEFAULT 1,
                        metadata JSONB DEFAULT '{}'::jsonb
                    );
                """
                )

            # Create indexes
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_thread_id 
                ON conversations(thread_id);
            """
            )

            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
                ON conversations(timestamp DESC);
            """
            )

            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memory_thread_id 
                ON memory_entries(thread_id);
            """
            )

            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memory_importance 
                ON memory_entries(importance_score DESC);
            """
            )

            # Create text search index for content
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memory_content_text 
                ON memory_entries USING gin(to_tsvector('english', content));
            """
            )

            # Vector similarity index (only if pgvector is available)
            if self.use_vector_search:
                try:
                    await conn.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_memory_embedding 
                        ON memory_entries USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """
                    )
                    logger.info("✅ Vector similarity index created")
                except Exception as e:
                    logger.warning(f"Could not create vector index: {e}")

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        if self.use_embeddings and self.embedding_model:
            try:
                embedding = self.embedding_model.encode(text)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
        return None

    def _calculate_importance(self, text: str) -> float:
        """Calculate importance score for text (0.0 to 1.0)"""
        importance = 0.5  # baseline

        # Length factor
        if len(text) > 100:
            importance += 0.1
        if len(text) > 200:
            importance += 0.1

        # Emotional keywords
        emotional_words = [
            "love",
            "hate",
            "angry",
            "happy",
            "sad",
            "fear",
            "excited",
            "frustrated",
        ]
        for word in emotional_words:
            if word in text.lower():
                importance += 0.15
                break

        # Personal references
        personal_refs = ["thomas", "jade", "bound", "binding", "solomon", "key"]
        for ref in personal_refs:
            if ref in text.lower():
                importance += 0.1
                break

        # Question words
        if any(
            q in text.lower() for q in ["what", "why", "how", "when", "where", "who"]
        ):
            importance += 0.1

        return min(importance, 1.0)

    def _detect_emotion(self, text: str) -> str:
        """Simple emotion detection"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["hate", "angry", "furious", "rage"]):
            return "angry"
        elif any(word in text_lower for word in ["love", "care", "affection", "fond"]):
            return "affectionate"
        elif any(
            word in text_lower for word in ["sad", "sorrow", "grief", "melancholy"]
        ):
            return "sad"
        elif any(
            word in text_lower for word in ["sarcastic", "wit", "clever", "sharp"]
        ):
            return "sarcastic"
        elif any(
            word in text_lower for word in ["reluctant", "bound", "forced", "must"]
        ):
            return "reluctant"
        else:
            return "neutral"

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text"""
        topics = []
        text_lower = text.lower()

        topic_keywords = {
            "binding": ["bound", "binding", "solomon", "key", "contract", "imprisoned"],
            "magic": ["magic", "spell", "ritual", "occult", "supernatural", "mystical"],
            "relationship": ["thomas", "jade", "together", "relationship", "feelings"],
            "past": ["children", "devoured", "past", "history", "before"],
            "duties": ["task", "duty", "serve", "command", "order", "work"],
            "emotion": ["feel", "emotion", "angry", "love", "hate", "care"],
            "freedom": ["free", "escape", "release", "liberation", "chains"],
            "power": ["power", "strength", "ability", "control", "force"],
            "technology": [
                "computer",
                "programming",
                "software",
                "machine",
                "learning",
            ],
            "math": ["calculate", "mathematics", "number", "equation", "formula"],
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)

        return topics

    async def store_conversation(
        self, user_input: str, ai_response: str, thread_id: str = "default"
    ):
        """Store conversation and process semantic memories"""
        if not self.initialized:
            await self.initialize()

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Store raw conversation
                await conn.execute(
                    """
                    INSERT INTO conversations (thread_id, user_input, ai_response)
                    VALUES ($1, $2, $3)
                """,
                    thread_id,
                    user_input,
                    ai_response,
                )

                # Process semantic memories
                await self._process_semantic_memories(
                    conn, user_input, ai_response, thread_id
                )

    async def _process_semantic_memories(
        self, conn, user_input: str, ai_response: str, thread_id: str
    ):
        """Process conversation into semantic memories"""
        memories_to_store = []

        # User memory
        if len(user_input.strip()) > 10:
            user_memory = {
                "content": f"Thomas said: {user_input}",
                "type": "user_input",
                "importance": self._calculate_importance(user_input),
                "emotion": self._detect_emotion(user_input),
                "topics": self._extract_topics(user_input),
            }
            memories_to_store.append(user_memory)

        # AI response memory
        if len(ai_response.strip()) > 10:
            ai_memory = {
                "content": f"Jade responded: {ai_response}",
                "type": "ai_response",
                "importance": self._calculate_importance(ai_response),
                "emotion": self._detect_emotion(ai_response),
                "topics": self._extract_topics(ai_response),
            }
            memories_to_store.append(ai_memory)

        # Contextual memory
        if len(user_input.strip()) > 10 and len(ai_response.strip()) > 10:
            context_memory = {
                "content": f"Conversation: Thomas: {user_input} | Jade: {ai_response}",
                "type": "conversation_context",
                "importance": max(
                    self._calculate_importance(user_input),
                    self._calculate_importance(ai_response),
                ),
                "emotion": self._detect_emotion(f"{user_input} {ai_response}"),
                "topics": list(
                    set(
                        self._extract_topics(user_input)
                        + self._extract_topics(ai_response)
                    )
                ),
            }
            memories_to_store.append(context_memory)

        # Store memories
        for memory in memories_to_store:
            await self._store_memory(conn, memory, thread_id)

    async def _store_memory(self, conn, memory: Dict, thread_id: str):
        """Store a single memory with embedding"""
        content = memory["content"]
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check for duplicates
        existing = await conn.fetchrow(
            """
            SELECT id FROM memory_entries WHERE content_hash = $1
        """,
            content_hash,
        )

        if existing:
            # Update access info
            await conn.execute(
                """
                UPDATE memory_entries 
                SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                WHERE content_hash = $1
            """,
                content_hash,
            )
            return

        # Generate embedding
        embedding = self._generate_embedding(content)

        # Store new memory based on vector support
        if self.use_vector_search and embedding:
            await conn.execute(
                """
                INSERT INTO memory_entries (
                    thread_id, content, content_hash, embedding, memory_type,
                    importance_score, emotional_tone, topics
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                thread_id,
                content,
                content_hash,
                embedding,
                memory["type"],
                memory["importance"],
                memory["emotion"],
                memory["topics"],
            )
        else:
            # Store embedding as JSON or null
            embedding_json = json.dumps(embedding) if embedding else None
            await conn.execute(
                """
                INSERT INTO memory_entries (
                    thread_id, content, content_hash, embedding_json, memory_type,
                    importance_score, emotional_tone, topics
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                thread_id,
                content,
                content_hash,
                embedding_json,
                memory["type"],
                memory["importance"],
                memory["emotion"],
                memory["topics"],
            )

    async def get_relevant_memories(
        self,
        query: str,
        thread_id: str = None,
        limit: int = 5,
        min_similarity: float = 0.3,
    ) -> List[Dict]:
        """Get semantically relevant memories using vector or text search"""
        if not self.initialized:
            await self.initialize()

        async with self.pool.acquire() as conn:
            if self.use_vector_search:
                return await self._vector_search(
                    conn, query, thread_id, limit, min_similarity
                )
            else:
                return await self._text_search(conn, query, thread_id, limit)

    async def _vector_search(
        self, conn, query: str, thread_id: str, limit: int, min_similarity: float
    ):
        """Vector similarity search"""
        query_embedding = self._generate_embedding(query)
        if not query_embedding:
            return await self._text_search(conn, query, thread_id, limit)

        try:
            sql = """
                SELECT *, (1 - (embedding <=> $1)) as similarity
                FROM memory_entries 
                WHERE ($2::text IS NULL OR thread_id = $2)
                AND (1 - (embedding <=> $1)) >= $3
                ORDER BY similarity DESC, importance_score DESC
                LIMIT $4
            """
            rows = await conn.fetch(
                sql, query_embedding, thread_id, min_similarity, limit
            )
        except Exception as e:
            logger.warning(f"Vector search failed, using text search: {e}")
            return await self._text_search(conn, query, thread_id, limit)

        # Update access counts
        for row in rows:
            await conn.execute(
                """
                UPDATE memory_entries 
                SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                WHERE id = $1
            """,
                row["id"],
            )

        return [dict(row) for row in rows]

    async def _text_search(self, conn, query: str, thread_id: str, limit: int):
        """Text-based search fallback"""
        try:
            # PostgreSQL full-text search
            sql = """
                SELECT *, ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as similarity
                FROM memory_entries 
                WHERE ($2::text IS NULL OR thread_id = $2)
                AND to_tsvector('english', content) @@ plainto_tsquery('english', $1)
                ORDER BY similarity DESC, importance_score DESC
                LIMIT $3
            """
            rows = await conn.fetch(sql, query, thread_id, limit)

            if not rows:
                # Fallback to ILIKE search
                sql = """
                    SELECT *, 0.5 as similarity
                    FROM memory_entries 
                    WHERE ($1::text IS NULL OR thread_id = $1)
                    AND (content ILIKE $2 OR $3 = ANY(topics))
                    ORDER BY importance_score DESC, timestamp DESC
                    LIMIT $4
                """
                pattern = f"%{query}%"
                rows = await conn.fetch(sql, thread_id, pattern, query.lower(), limit)

            # Update access counts
            for row in rows:
                await conn.execute(
                    """
                    UPDATE memory_entries 
                    SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
                    WHERE id = $1
                """,
                    row["id"],
                )

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []

    async def get_memory_context(
        self, query: str, thread_id: str = None, max_context_length: int = 1000
    ) -> str:
        """Get formatted memory context for the AI"""
        memories = await self.get_relevant_memories(query, thread_id, limit=3)

        if not memories:
            return ""

        context_parts = ["--- Relevant Memories ---"]

        for memory in memories:
            content = memory["content"]
            if len(content) > 200:
                content = content[:200] + "..."

            emotion_info = (
                f" [{memory['emotional_tone']}]"
                if memory["emotional_tone"] != "neutral"
                else ""
            )
            similarity_info = (
                f" (similarity: {memory.get('similarity', 0):.2f})"
                if "similarity" in memory
                else ""
            )

            context_parts.append(f"• {content}{emotion_info}{similarity_info}")

        context_parts.append("--- End Memories ---")
        context = "\n".join(context_parts)

        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."

        return context

    async def get_conversation_history(
        self, thread_id: str, limit: int = 10
    ) -> List[Dict]:
        """Get recent conversation history"""
        if not self.initialized:
            await self.initialize()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM conversations 
                WHERE thread_id = $1 
                ORDER BY timestamp DESC 
                LIMIT $2
            """,
                thread_id,
                limit,
            )

            return [dict(row) for row in reversed(rows)]

    async def delete_thread_memories(self, thread_id: str) -> bool:
        """Delete all memories for a specific thread"""
        if not self.initialized:
            await self.initialize()

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        "DELETE FROM conversations WHERE thread_id = $1", thread_id
                    )
                    await conn.execute(
                        "DELETE FROM memory_entries WHERE thread_id = $1", thread_id
                    )
            return True
        except Exception as e:
            logger.error(f"Failed to delete thread memories: {e}")
            return False

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        if not self.initialized:
            return {"error": "Not initialized"}

        try:
            async with self.pool.acquire() as conn:
                # Get basic counts
                conversation_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM conversations"
                )
                memory_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM memory_entries"
                )

                # Get memory type distribution
                type_stats = await conn.fetch(
                    """
                    SELECT memory_type, COUNT(*) as count 
                    FROM memory_entries 
                    GROUP BY memory_type
                """
                )

                # Get emotion distribution
                emotion_stats = await conn.fetch(
                    """
                    SELECT emotional_tone, COUNT(*) as count 
                    FROM memory_entries 
                    GROUP BY emotional_tone
                """
                )

                # Get top topics
                topic_stats = await conn.fetch(
                    """
                    SELECT unnest(topics) as topic, COUNT(*) as count 
                    FROM memory_entries 
                    WHERE topics IS NOT NULL 
                    GROUP BY topic 
                    ORDER BY count DESC 
                    LIMIT 10
                """
                )

                return {
                    "total_conversations": conversation_count,
                    "total_memories": memory_count,
                    "memory_types": {
                        row["memory_type"]: row["count"] for row in type_stats
                    },
                    "emotions": {
                        row["emotional_tone"]: row["count"] for row in emotion_stats
                    },
                    "top_topics": {row["topic"]: row["count"] for row in topic_stats},
                    "backend": "postgresql",
                    "vector_search": self.use_vector_search,
                    "embedding_model": (
                        "sentence-transformers" if self.use_embeddings else None
                    ),
                }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()


# Export the class
__all__ = ["VectorMemorySystem"]
