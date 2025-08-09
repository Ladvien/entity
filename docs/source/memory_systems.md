# Memory Systems - Agents That Remember

## Why Memory Matters

Without memory, agents are like goldfish - every conversation starts from scratch. Entity's memory system enables agents to remember conversations, learn from interactions, and build relationships with users over time.

## Memory Architecture: Two Types of Storage

Entity provides two complementary memory systems:

### 1. Structured Memory (Database) 🗃️
- **Key-value storage** for facts and preferences
- **Conversation history** for context continuity
- **User profiles** and settings
- **Cross-process safe** with file locking

### 2. Semantic Memory (Vector Store) 🧠
- **Embedding-based** similarity search
- **Semantic relationships** between concepts
- **Long-term knowledge** retention
- **Context-aware** retrieval

## Quick Example: Remembering User Preferences

```python
# Without memory
agent = Agent(resources=load_defaults())
await agent.chat("I love Python programming")
await agent.chat("What do I like?")
# "I don't have information about your preferences"

# With memory (automatic in Entity!)
agent = Agent(resources=load_defaults())
await agent.chat("I love Python programming", user_id="alice")
await agent.chat("What do I like?", user_id="alice")
# "Based on our conversation, you love Python programming!"
```

## How Memory Works in Entity

### Automatic Context Preservation

Entity automatically provides memory context to plugins:

```python
from entity.plugins.base import Plugin

class MemoryAwarePlugin(Plugin):
    async def _execute_impl(self, context):
        # Remember something
        await context.remember("user_language", "Python")

        # Recall something later
        language = await context.recall("user_language")

        # User isolation is automatic!
        # Alice's memories ≠ Bob's memories

        return f"Your preferred language is {language}"
```

### Memory in the 6-Stage Pipeline

```
INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
  ↓       ↓       ↓     ↓      ↓        ↓
  🧠 Memory is accessible at every stage 🧠
```

## Core Memory Operations

### Basic Key-Value Storage

```python
# In any plugin with memory access:
async def _execute_impl(self, context):
    # Store information
    await context.remember("name", "Alice")
    await context.remember("age", 25)
    await context.remember("preferences", {
        "language": "Python",
        "framework": "FastAPI",
        "editor": "VSCode"
    })

    # Retrieve information
    name = await context.recall("name")  # "Alice"
    age = await context.recall("age")    # 25
    prefs = await context.recall("preferences")  # {...}

    # With defaults for missing keys
    city = await context.recall("city", "Unknown")  # "Unknown"

    return f"Hello {name}, age {age}"
```

### User Isolation by Default

```python
# User Alice
await context.remember("favorite_color", "blue")  # user_id="alice"

# User Bob
await context.remember("favorite_color", "red")   # user_id="bob"

# Later...
alice_color = await context.recall("favorite_color")  # "blue"
bob_color = await context.recall("favorite_color")    # "red"

# Memories are automatically namespaced by user_id!
```

### Conversation History

Entity automatically maintains conversation history:

```python
class ContextAwarePlugin(Plugin):
    async def _execute_impl(self, context):
        # Access conversation history
        history = await context.recall("conversation_history", [])

        # Add current message
        history.append({
            "timestamp": datetime.now().isoformat(),
            "message": context.message,
            "response": "Generated response here"
        })

        # Update history (with size limit)
        if len(history) > 50:
            history = history[-50:]  # Keep last 50 messages

        await context.remember("conversation_history", history)

        # Use history for context-aware responses
        recent_topics = self._extract_topics(history[-10:])
        return f"Continuing our discussion about {recent_topics}"
```

## Advanced Memory Patterns

### Learning User Preferences

```python
class AdaptiveLearningPlugin(Plugin):
    """Plugin that learns and adapts to user preferences."""

    async def _execute_impl(self, context):
        message = context.message.lower()

        # Detect preferences from conversation
        preferences = await context.recall("preferences", {})

        if "i love" in message or "i like" in message:
            # Extract what they like
            liked_item = self._extract_preference(message)
            preferences.setdefault("likes", []).append(liked_item)

        elif "i hate" in message or "i dislike" in message:
            # Extract what they dislike
            disliked_item = self._extract_preference(message)
            preferences.setdefault("dislikes", []).append(disliked_item)

        # Save updated preferences
        await context.remember("preferences", preferences)

        # Adapt response based on preferences
        return self._personalized_response(context.message, preferences)
```

### Skill Development Tracking

```python
class SkillTrackerPlugin(Plugin):
    """Track user's learning progress over time."""

    async def _execute_impl(self, context):
        skills = await context.recall("skills", {})

        # Detect learning activities
        if "learned" in context.message or "understand" in context.message:
            topic = self._extract_topic(context.message)

            if topic not in skills:
                skills[topic] = {
                    "level": 1,
                    "first_encounter": datetime.now().isoformat(),
                    "interactions": 0
                }

            # Level up based on interactions
            skills[topic]["interactions"] += 1
            if skills[topic]["interactions"] % 5 == 0:
                skills[topic]["level"] += 1

            await context.remember("skills", skills)

            level = skills[topic]["level"]
            return f"Great! You're now level {level} in {topic}!"

        return "How can I help you learn today?"
```

### Relationship Building

```python
class RelationshipPlugin(Plugin):
    """Build deeper relationships through memory."""

    async def _execute_impl(self, context):
        relationship = await context.recall("relationship_data", {
            "interactions": 0,
            "last_seen": None,
            "mood_history": [],
            "personal_info": {},
            "relationship_stage": "stranger"
        })

        # Update interaction count
        relationship["interactions"] += 1
        relationship["last_seen"] = datetime.now().isoformat()

        # Analyze current mood
        mood = self._detect_mood(context.message)
        relationship["mood_history"].append(mood)

        # Evolve relationship stage
        if relationship["interactions"] > 10:
            relationship["relationship_stage"] = "acquaintance"
        if relationship["interactions"] > 50:
            relationship["relationship_stage"] = "friend"

        await context.remember("relationship_data", relationship)

        # Respond based on relationship stage
        stage = relationship["relationship_stage"]
        if stage == "friend":
            return f"Hey friend! Good to see you again. How are you feeling today?"
        elif stage == "acquaintance":
            return f"Nice to chat with you again! We've talked {relationship['interactions']} times now."
        else:
            return "Hello! I'm getting to know you."
```

## Memory Configuration

### Basic Memory Settings

```yaml
# agent_config.yaml
resources:
  memory:
    # Database settings
    persistence: true           # Save to disk vs in-memory only
    database_path: "./memories" # Where to store database

    # Vector store settings
    embedding_model: "all-MiniLM-L6-v2"  # For semantic memory
    vector_dimensions: 384               # Embedding size

    # Performance tuning
    cache_size: 1000           # In-memory cache for frequent access
    batch_size: 100            # Batch operations for efficiency
```

### Advanced Memory Configuration

```yaml
resources:
  memory:
    # Multiple memory backends
    structured_storage:
      type: "duckdb"
      path: "./agent_memory.duckdb"
      pool_size: 5

    semantic_storage:
      type: "vector_store"
      backend: "duckdb"  # or "chroma", "pinecone"
      embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

    # Memory policies
    retention:
      conversation_history: 1000    # Messages to keep
      user_preferences: unlimited   # Keep forever
      skill_tracking: unlimited     # Keep forever
      temporary_data: 24           # Hours before cleanup

    # Privacy settings
    encryption:
      enabled: true
      key_rotation: daily

    # Cross-process safety
    locking:
      enabled: true
      timeout: 5.0  # Seconds
```

## Memory Best Practices

### DO: Namespace Your Data
```python
# Good: Clear namespacing
await context.remember("learning:python_level", 5)
await context.remember("preferences:color", "blue")
await context.remember("profile:name", "Alice")

# Avoid: Generic keys
await context.remember("level", 5)     # Level of what?
await context.remember("data", {...})  # What data?
```

### DO: Handle Memory Failures
```python
async def _execute_impl(self, context):
    try:
        user_prefs = await context.recall("preferences")
        return self._personalized_response(user_prefs)
    except Exception as e:
        # Fallback to default behavior
        context.logger.warning(f"Memory access failed: {e}")
        return self._default_response()
```

### DO: Implement Memory Limits
```python
async def _execute_impl(self, context):
    history = await context.recall("conversation_history", [])

    # Add new message
    history.append(new_message)

    # Implement sliding window
    MAX_HISTORY = 100
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    await context.remember("conversation_history", history)
```

### DON'T: Store Sensitive Data
```python
# ❌ Don't store passwords, API keys, personal data
await context.remember("password", user_password)
await context.remember("ssn", social_security)

# ✅ Store preferences, settings, learning progress
await context.remember("ui_theme", "dark")
await context.remember("skill_level", "intermediate")
```

### DON'T: Create Memory Leaks
```python
# ❌ Unbounded growth
history = await context.recall("all_messages", [])
history.append(new_message)  # Grows forever!

# ✅ Bounded with cleanup
MAX_SIZE = 1000
history = await context.recall("recent_messages", [])
history.append(new_message)
if len(history) > MAX_SIZE:
    history = history[-MAX_SIZE:]
```

## Testing Memory Systems

```python
import pytest
from entity.plugins.context import Context
from entity.resources.memory import Memory

@pytest.mark.asyncio
async def test_memory_persistence():
    # Create test context with memory
    context = Context(
        message="test message",
        resources={"memory": memory_instance},
        user_id="test_user"
    )

    # Test remember/recall cycle
    await context.remember("test_key", "test_value")
    result = await context.recall("test_key")
    assert result == "test_value"

@pytest.mark.asyncio
async def test_user_isolation():
    # Alice stores a value
    alice_context = Context("", {"memory": memory}, "alice")
    await alice_context.remember("name", "Alice")

    # Bob stores a different value
    bob_context = Context("", {"memory": memory}, "bob")
    await bob_context.remember("name", "Bob")

    # Verify isolation
    alice_name = await alice_context.recall("name")
    bob_name = await bob_context.recall("name")

    assert alice_name == "Alice"
    assert bob_name == "Bob"
```

## Memory Debugging

### Memory Inspector Plugin
```python
class MemoryInspectorPlugin(Plugin):
    """Debug plugin to inspect memory state."""

    async def _execute_impl(self, context):
        if context.message.startswith("/memory"):
            # Show all stored keys for this user
            all_keys = await self._get_user_keys(context)
            return f"Your memory contains: {', '.join(all_keys)}"

        elif context.message.startswith("/forget"):
            key = context.message.split(" ", 1)[1]
            await context.remember(key, None)  # Clear the key
            return f"Forgot {key}"

        return "Memory commands: /memory, /forget <key>"
```

## Memory Performance Tips

### Batch Operations
```python
# ❌ Slow: Multiple individual operations
await context.remember("key1", value1)
await context.remember("key2", value2)
await context.remember("key3", value3)

# ✅ Fast: Batch related data
batch_data = {
    "key1": value1,
    "key2": value2,
    "key3": value3
}
await context.remember("batch_data", batch_data)
```

### Lazy Loading
```python
# ✅ Load memory data only when needed
async def _execute_impl(self, context):
    if self._needs_user_history():
        history = await context.recall("conversation_history", [])
        # Process history...
    else:
        # Skip loading if not needed
        pass
```

## Next Steps

- **[Streaming Responses](streaming_responses.md)**: Real-time memory updates
- **[Custom Plugin Development](plugin_development.md)**: Advanced memory patterns
- **[Production Deployment](production_deployment.md)**: Memory at scale

Remember: **Memory transforms agents from tools to companions!**
