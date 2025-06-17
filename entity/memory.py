# entity/memory/__init__.py (replace the placeholder)

import asyncio
import logging
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class VectorMemorySystem:
    """Vector memory system with local storage fallback"""

    def __init__(self, settings=None):
        self.settings = settings
        self.initialized = False

        # In-memory storage for conversations and memories
        self.conversations = []  # List of conversation dicts
        self.memories = []  # List of memory dicts with embeddings
        self.conversation_count = 0

        # Simple embedding simulation (in real implementation, use sentence-transformers)
        self.use_real_embeddings = False
        try:
            from sentence_transformers import SentenceTransformer

            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.use_real_embeddings = True
            self.embedding_dim = 384
        except ImportError:
            print("⚠️  sentence-transformers not available, using simple embeddings")
            self.embedding_model = None
            self.embedding_dim = 50  # Simple embedding size

    async def initialize(self):
        """Initialize the memory system"""
        if self.initialized:
            return

        print("🧠 Initializing Vector Memory System (in-memory)")

        if self.use_real_embeddings:
            print("✅ Using sentence-transformers for embeddings")
        else:
            print("⚠️  Using simple hash-based embeddings")

        self.initialized = True

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        if self.use_real_embeddings and self.embedding_model:
            return self.embedding_model.encode(text)
        else:
            # Simple hash-based embedding fallback
            text_hash = hashlib.md5(text.encode()).hexdigest()
            # Convert hash to numbers
            numbers = [ord(c) for c in text_hash[: self.embedding_dim]]
            # Pad or truncate to correct size
            while len(numbers) < self.embedding_dim:
                numbers.append(0)
            return np.array(numbers[: self.embedding_dim], dtype=np.float32)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            return dot_product / (norm_a * norm_b)
        except:
            return 0.0

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

        # Question words (indicate important information seeking)
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

        # Predefined topic keywords
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
        """Store conversation with semantic processing"""
        if not self.initialized:
            await self.initialize()

        try:
            self.conversation_count += 1

            # Store raw conversation
            conversation = {
                "id": self.conversation_count,
                "thread_id": thread_id,
                "user_input": user_input,
                "ai_response": ai_response,
                "timestamp": datetime.now(),
                "metadata": {},
            }
            self.conversations.append(conversation)

            # Process and store semantic memories
            await self._process_semantic_memory(user_input, ai_response, thread_id)

            logger.debug(
                f"Stored conversation #{self.conversation_count} for thread {thread_id}"
            )

        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")

    async def _process_semantic_memory(
        self, user_input: str, ai_response: str, thread_id: str
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

        # Contextual memory (conversation pair)
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

        # Store all memories
        for memory in memories_to_store:
            await self._store_memory(memory, thread_id)

    async def _store_memory(self, memory: Dict, thread_id: str):
        """Store a single memory with embedding"""
        content = memory["content"]
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if we already have this memory
        for existing_memory in self.memories:
            if existing_memory.get("content_hash") == content_hash:
                # Update access info
                existing_memory["last_accessed"] = datetime.now()
                existing_memory["access_count"] = (
                    existing_memory.get("access_count", 0) + 1
                )
                return

        # Generate embedding
        embedding = self._generate_embedding(content)

        # Store new memory
        memory_entry = {
            "id": len(self.memories) + 1,
            "thread_id": thread_id,
            "content": content,
            "content_hash": content_hash,
            "embedding": embedding,
            "memory_type": memory["type"],
            "importance_score": memory["importance"],
            "emotional_tone": memory["emotion"],
            "topics": memory["topics"],
            "timestamp": datetime.now(),
            "last_accessed": datetime.now(),
            "access_count": 1,
            "metadata": {},
        }

        self.memories.append(memory_entry)

    async def get_relevant_memories(
        self,
        query: str,
        thread_id: str = None,
        limit: int = 5,
        min_similarity: float = 0.3,
    ) -> List[Dict]:
        """Get semantically relevant memories"""
        if not self.initialized:
            await self.initialize()

        if not self.memories:
            return []

        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)

            # Calculate similarities
            memory_similarities = []
            for memory in self.memories:
                # Optional thread filtering
                if thread_id and memory.get("thread_id") != thread_id:
                    continue

                similarity = self._cosine_similarity(
                    query_embedding, memory["embedding"]
                )

                if similarity >= min_similarity:
                    memory_copy = memory.copy()
                    memory_copy["similarity"] = similarity
                    memory_similarities.append(memory_copy)

            # Sort by similarity and importance
            memory_similarities.sort(
                key=lambda x: (x["similarity"], x["importance_score"]), reverse=True
            )

            # Update access counts for retrieved memories
            for memory in memory_similarities[:limit]:
                original_memory = next(
                    m for m in self.memories if m["id"] == memory["id"]
                )
                original_memory["last_accessed"] = datetime.now()
                original_memory["access_count"] = (
                    original_memory.get("access_count", 0) + 1
                )

            return memory_similarities[:limit]

        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []

    async def get_memory_context(
        self, query: str, thread_id: str = None, max_context_length: int = 1000
    ) -> str:
        """Get formatted memory context for the AI"""
        if not self.initialized:
            return ""

        try:
            # Get relevant memories
            memories = await self.get_relevant_memories(query, thread_id, limit=3)

            if not memories:
                return ""

            # Format context
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
                context_parts.append(f"• {content}{emotion_info}")

            context_parts.append("--- End Memories ---")

            context = "\n".join(context_parts)

            # Ensure we don't exceed max length
            if len(context) > max_context_length:
                context = context[:max_context_length] + "..."

            return context

        except Exception as e:
            logger.error(f"Failed to get memory context: {e}")
            return ""

    async def get_conversation_history(
        self, thread_id: str, limit: int = 10
    ) -> List[Dict]:
        """Get recent conversation history"""
        if not self.initialized:
            return []

        # Filter conversations by thread_id
        thread_conversations = [
            conv for conv in self.conversations if conv["thread_id"] == thread_id
        ]

        # Sort by timestamp and get most recent
        thread_conversations.sort(key=lambda x: x["timestamp"], reverse=True)

        return thread_conversations[:limit]

    async def delete_thread_memories(self, thread_id: str) -> bool:
        """Delete all memories for a specific thread"""
        try:
            # Remove conversations
            self.conversations = [
                conv for conv in self.conversations if conv["thread_id"] != thread_id
            ]

            # Remove memories
            self.memories = [
                mem for mem in self.memories if mem.get("thread_id") != thread_id
            ]

            return True

        except Exception as e:
            logger.error(f"Failed to delete thread memories: {e}")
            return False

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        if not self.initialized:
            return {"error": "Not initialized"}

        try:
            # Calculate statistics
            memory_types = {}
            emotions = {}
            topics = {}

            for memory in self.memories:
                # Memory types
                mem_type = memory.get("memory_type", "unknown")
                memory_types[mem_type] = memory_types.get(mem_type, 0) + 1

                # Emotions
                emotion = memory.get("emotional_tone", "unknown")
                emotions[emotion] = emotions.get(emotion, 0) + 1

                # Topics
                for topic in memory.get("topics", []):
                    topics[topic] = topics.get(topic, 0) + 1

            # Get top topics
            top_topics = dict(
                sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]
            )

            return {
                "entity_id": (
                    self.settings.entity.entity_id
                    if self.settings and hasattr(self.settings, "entity")
                    else "unknown"
                ),
                "total_memories": len(self.memories),
                "total_conversations": len(self.conversations),
                "memory_types": memory_types,
                "emotions": emotions,
                "top_topics": top_topics,
                "embedding_model": (
                    "sentence-transformers" if self.use_real_embeddings else "simple"
                ),
                "embedding_dimension": self.embedding_dim,
                "backend": "in-memory",
                "config": {
                    "initialized": self.initialized,
                    "conversation_count": self.conversation_count,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close connections (no-op for in-memory)"""
        pass


# Export the class
__all__ = ["VectorMemorySystem"]
