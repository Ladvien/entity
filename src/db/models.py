# src/db/models.py

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, JSON, Text
from datetime import datetime
import uuid

Base = declarative_base()


class ChatInteractionORM(Base):
    __tablename__ = "chat_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interaction_id = Column(
        String, unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    thread_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    raw_input = Column(Text, nullable=False)
    raw_output = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    tools_used = Column(JSON, default=list)
    memory_context_used = Column(Boolean, default=False)
    memory_context = Column(Text, default="")
    use_tools = Column(Boolean, default=True)
    use_memory = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    conversation_turn = Column(Integer, nullable=True)
    user_id = Column(String, nullable=True)
    agent_personality_applied = Column(Boolean, default=False)
    personality_adjustments = Column(JSON, default=list)

    # to something like:
    extra_metadata = Column("metadata", JSON, default=dict)
