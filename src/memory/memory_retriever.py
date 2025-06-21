from typing import List, Optional
from src.memory.memory_system import MemorySystem
from langchain_core.documents import Document


class MemoryRetriever:
    def __init__(self, memory_system: MemorySystem):
        self.memory_system = memory_system

    async def search(
        self, query: str, thread_id: Optional[str] = None, k: int = 5
    ) -> List[Document]:
        """Semantic search using vector store only."""
        return await self.memory_system.search_memory(query, thread_id=thread_id, k=k)

    async def deep_search(
        self, query: str, thread_id: Optional[str] = None, k: int = 5
    ) -> List[Document]:
        """Semantic + keyword search through vector store and chat history."""
        vector_results = await self.search(query, thread_id, k)

        chat_interactions = await self.memory_system.search_chat_history(
            query, thread_id, k
        )
        chat_docs = [
            Document(
                page_content=f"{i.raw_input}\n---\n{i.raw_output}",
                metadata={
                    "thread_id": i.thread_id,
                    "interaction_id": i.interaction_id,
                    "timestamp": i.timestamp.isoformat(),
                    "type": "chat",
                },
            )
            for i in chat_interactions
        ]

        # Combine and return top-k (you could sort or filter if needed)
        return (vector_results + chat_docs)[:k]
