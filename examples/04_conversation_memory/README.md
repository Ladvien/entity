# 04 - Conversation Memory 🧠

**Build Agents That Remember and Learn**

Discover Entity's powerful memory system that enables agents to maintain context, remember user preferences, and build long-term relationships.

## What This Example Teaches

- 🧠 **Persistent memory** across sessions
- 👤 **User preferences** and personalization
- 🔗 **Context awareness** for better responses
- 📊 **Memory management** and optimization
- 🎯 **Long-term relationship building**

## The Memory-Enabled Agent

```python
#!/usr/bin/env python3
"""
Conversation Memory Example - Agents That Remember

Demonstrates Entity's powerful memory system for maintaining
context, user preferences, and long-term conversational state.
"""

import asyncio
from pathlib import Path
from entity import Agent

async def main():
    \"\"\"Run a memory-enabled agent.\"\"\"

    print("🧠 Entity Agent with Advanced Memory")
    print("=" * 38)
    print()
    print("This agent demonstrates:")
    print("💾 Persistent memory across sessions")
    print("👤 User preference learning and recall")
    print("🔗 Context-aware conversations")
    print("📈 Relationship building over time")
    print()

    config_path = Path(__file__).parent / "memory_config.yaml"

    try:
        agent = Agent.from_config(str(config_path))

        print("✅ Memory-enabled agent loaded!")
        print()
        print("🧪 Try these memory features:")
        print("   • 'My name is Alice and I love Python'")
        print("   • 'What's my name?' (in a new session)")
        print("   • 'Remember that I prefer detailed explanations'")
        print("   • 'What do you know about my preferences?'")
        print("   • 'We discussed decorators last time'")
        print()
        print("🔄 Restart the agent - it will remember everything!")
        print("=" * 38)

        await agent.chat("")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Memory Configuration (`memory_config.yaml`)

```yaml
# Memory-Enabled Agent Configuration
# Demonstrates advanced memory and context management

role: |
  You are an AI assistant with an excellent memory system.

  Your memory capabilities:
  - Remember user names, preferences, and personal details
  - Recall previous conversations and topics discussed
  - Track learning progress and interests over time
  - Build long-term relationships through consistent interactions
  - Use context from past sessions to provide better responses

  Your approach:
  - Always greet returning users by name when possible
  - Reference previous conversations naturally
  - Ask follow-up questions based on past interactions
  - Adapt your communication style to user preferences
  - Celebrate progress and milestones you've observed

# Enhanced memory settings
resources:
  memory:
    # Persistent storage across sessions
    persistence: true

    # Extended context retention
    context_window: 8000
    conversation_history_length: 100

    # User preference tracking
    track_preferences: true
    preference_categories:
      - communication_style  # formal, casual, technical
      - explanation_depth    # brief, detailed, comprehensive
      - topic_interests      # programming, data science, web dev
      - learning_pace       # fast, moderate, slow
      - preferred_examples  # theoretical, practical, real-world

    # Long-term memory features
    relationship_building: true
    milestone_tracking: true
    session_summaries: true

  llm:
    temperature: 0.4  # Balanced for consistent personality
    max_tokens: 2500
```

## Advanced Memory Features

### 🔍 **Context Retrieval**
```python
# The agent automatically accesses relevant context:
# - Recent conversation history
# - User preferences and details
# - Previously discussed topics
# - Relationship milestones
```

### 📊 **Preference Learning**
```python
# Agent learns and adapts to:
user_preferences = {
    "communication_style": "technical_but_friendly",
    "explanation_depth": "detailed_with_examples",
    "topics_of_interest": ["python", "machine_learning"],
    "preferred_pace": "moderate_with_practice",
    "learning_goals": ["become_data_scientist"]
}
```

### 🎯 **Relationship Building**
```python
# Agent tracks relationship milestones:
relationship_data = {
    "first_interaction": "2024-01-15",
    "total_sessions": 23,
    "topics_explored": ["python_basics", "pandas", "ml_algorithms"],
    "progress_markers": ["completed_first_project", "understood_decorators"],
    "personal_details": {"name": "Alice", "role": "student", "goals": ["data_science"]}
}
```

## Example Conversations

### First Session
```
👤 Alice: Hi, I'm Alice and I'm learning Python. I prefer detailed explanations.

🤖 Agent: Hello Alice! It's great to meet you. I'm excited to help you learn Python!

I've noted that you prefer detailed explanations - I'll make sure to provide comprehensive answers with plenty of examples and context.

Since you're learning Python, what specific areas are you most interested in? Are you working towards any particular goals like web development, data science, or automation?

I'll remember our conversation for next time so we can build on what we discuss today.
```

### Second Session (Days Later)
```
👤 Alice: I'm back!

🤖 Agent: Welcome back, Alice! Great to see you again!

Last time we discussed your Python learning journey and I remember you prefer detailed explanations. Since our first conversation, I've been looking forward to hearing about your progress.

How has your Python learning been going? Did you get a chance to work on any of the topics we discussed, or do you have new questions that have come up in your studies?
```

### Third Session (Weeks Later)
```
👤 Alice: I've been working on that pandas project we talked about.

🤖 Agent: That's fantastic, Alice! I remember you were excited about diving into data analysis with pandas. It's wonderful that you've made progress on the project we discussed.

How is it going? From our previous conversations, I know you like detailed explanations, so I'd love to hear about:
- What specific challenges you've encountered
- Which pandas concepts are clicking for you
- Any "aha!" moments you've had

Based on your learning style and our past discussions, I can provide targeted help with any specific issues you're facing. You've made great progress since we started - from Python basics to working on real pandas projects!
```

### Preference Adaptation
```
👤 Alice: Can you give me a quick summary this time? I'm short on time.

🤖 Agent: Of course, Alice! I notice this is different from your usual preference for detailed explanations - no problem adapting to your current needs.

**Quick pandas tip:** Use `df.describe()` for instant statistical summary of your data.

I'll remember you sometimes need brief answers when you're pressed for time, while keeping your general preference for detailed explanations when you have more time to dive deep.

Anything else you need a quick answer on?
```

## Memory Management Commands

The agent can manage its own memory:

```
👤 You: What do you remember about me?

🤖 Agent: Here's what I remember about you, Alice:

**Personal Details:**
- Name: Alice
- Learning focus: Python and data science
- Communication preference: Usually detailed, sometimes brief when busy

**Our Journey Together:**
- First met: 3 weeks ago
- Total conversations: 8 sessions
- Topics we've explored: Python basics → pandas → data analysis projects

**Your Progress:**
- ✅ Mastered Python fundamentals
- ✅ Built first pandas project
- 🔄 Currently working on data visualization
- 🎯 Goal: Become proficient in data science

**Preferences I've Learned:**
- Explanation style: Detailed with examples
- Learning pace: Steady with hands-on practice
- Example preference: Real-world applications

Is there anything you'd like me to remember differently or any details to update?
```

## Memory Privacy & Control

```yaml
# Privacy settings in config
memory:
  privacy:
    user_consent_required: true
    data_retention_days: 90  # Auto-delete old data
    export_allowed: true     # User can export their data
    delete_on_request: true  # User can delete their data

  user_control:
    view_memory: true        # User can see what's remembered
    edit_memory: true        # User can correct information
    selective_forget: true   # User can delete specific memories
```

## Running the Example

```bash
cd examples/04_conversation_memory
pip install -r requirements.txt
python memory_agent.py
```

## Key Benefits

### 🧠 **Intelligent Context**
- Agents provide increasingly relevant responses
- No need to repeat context in each conversation
- Natural relationship building over time

### 🎯 **Personalization**
- Adapts to individual communication styles
- Remembers user goals and preferences
- Provides customized learning experiences

### 📈 **Continuous Improvement**
- Gets better at helping each user over time
- Tracks progress and celebrates milestones
- Suggests next steps based on history

### 🔒 **Privacy & Control**
- User controls what is remembered
- Data retention policies
- Easy memory management and deletion

## Next Steps

1. **Try the memory agent**: Have conversations across multiple sessions
2. **Test personalization**: Tell it your preferences and see them applied
3. **Explore privacy features**: Manage your memory data
4. **Ready for streaming?**: Check out [05_streaming_responses](../05_streaming_responses/)

## Key Concepts Learned

✅ **Persistent Memory** across sessions and interactions
✅ **User Preference Learning** for personalized experiences
✅ **Context Awareness** for intelligent responses
✅ **Relationship Building** through long-term memory
✅ **Privacy Controls** for user data management

---

**🎉 Excellent!** You've learned how to build agents that truly remember and learn from interactions. This creates much more engaging and helpful AI assistants.

*← Previous: [Tool Usage](../03_tool_usage/) | Next: [Streaming Responses](../05_streaming_responses/) →*
