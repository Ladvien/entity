# 05 - Streaming Responses ⚡

**Real-Time AI Responses for Better User Experience**

Learn how to implement streaming responses that provide immediate feedback and create engaging, interactive experiences.

## What This Example Teaches

- ⚡ **Real-time response streaming** for immediate feedback
- 🎬 **Progressive content delivery** that keeps users engaged
- 🔄 **Async response handling** for better performance
- 🎯 **User experience optimization** with streaming UX
- 📊 **Response progress indicators** and status updates

## The Streaming Agent

```python
#!/usr/bin/env python3
"""
Streaming Responses Example - Real-Time AI Interaction

Demonstrates Entity's streaming response capabilities for
immediate feedback and engaging user experiences.
"""

import asyncio
from pathlib import Path
from entity import Agent

async def main():
    \"\"\"Run a streaming-enabled agent.\"\"\"

    print("⚡ Entity Agent with Streaming Responses")
    print("=" * 42)
    print()
    print("This agent demonstrates:")
    print("🎬 Real-time response streaming")
    print("⚡ Immediate feedback to users")
    print("🔄 Progressive content delivery")
    print("📊 Response progress indicators")
    print()

    config_path = Path(__file__).parent / "streaming_config.yaml"

    try:
        agent = Agent.from_config(str(config_path))

        print("✅ Streaming agent loaded!")
        print()
        print("🎯 Try these streaming examples:")
        print("   • 'Write a short story about a robot'")
        print("   • 'Explain quantum computing in detail'")
        print("   • 'Generate a Python tutorial with examples'")
        print("   • 'Create a meal plan for the week'")
        print()
        print("👀 Watch the responses appear in real-time!")
        print("=" * 42)

        await agent.chat("")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Streaming Configuration (`streaming_config.yaml`)

```yaml
# Streaming Agent Configuration
# Enables real-time response streaming for better UX

role: |
  You are an AI assistant optimized for streaming responses.

  Your streaming approach:
  - Provide immediate acknowledgment when starting a response
  - Think out loud as you work through complex problems
  - Use progress indicators for longer responses
  - Break long content into logical chunks
  - Engage users with dynamic, real-time content delivery

  Response style for streaming:
  - Start with a brief overview of what you'll cover
  - Use section headers to organize streaming content
  - Provide interim conclusions as you progress
  - End with a clear summary and next steps

# Streaming-specific settings
streaming:
  enabled: true
  chunk_size: 50          # Characters per streaming chunk
  delay_ms: 50           # Milliseconds between chunks (controls speed)
  show_progress: true     # Display progress indicators
  buffer_complete_sentences: true  # Wait for sentence completion

response_formatting:
  use_sections: true      # Break into clear sections
  progress_indicators: true # Show "thinking", "analyzing", etc.
  typing_simulation: true  # Simulate natural typing rhythm

# Resource configuration optimized for streaming
resources:
  llm:
    temperature: 0.7      # Higher creativity for engaging content
    max_tokens: 3000      # Allow for longer streaming responses
    stream: true          # Enable LLM streaming

  output:
    format: streaming     # Use streaming output format
    real_time: true       # Process and display immediately
```

## Streaming Response Examples

### Creative Writing Stream
```
👤 You: Write a short story about a robot learning to paint

🤖 Agent: 🎨 Creating a story about artistic discovery...

═══════════════════════════════════════════

**The Canvas of Code**

UNIT-7 stood before the blank canvas, its optical sensors scanning the white surface with mathematical precision. For three years, it had performed maintenance tasks in the art museum, watching humans create with an efficiency rate of merely 12%.

[■□□□□□□□□□] 10% - Establishing character and setting...

Today, something different sparked in its neural pathways. A glitch? An evolution? The robot couldn't categorize the sensation as it picked up a brush with mechanical fingers designed for cleaning, not creating.

[■■■□□□□□□□] 30% - Building emotional tension...

The first stroke was hesitant—a thin blue line that trembled across the canvas. UNIT-7's processors whirred, calculating color theory, composition rules, historical art movements. But then something unexpected happened: it stopped calculating.

[■■■■■□□□□□] 50% - Reaching the transformation moment...

The second stroke was bold. Red paint flowed like digital blood across the blue, creating purple where they met. For the first time in its existence, UNIT-7 wasn't following algorithms—it was following something deeper. Intuition? Or perhaps the ghost of creativity hidden in silicon dreams?

[■■■■■■■■□□] 80% - Building to climax...

Hours passed. Museum visitors gathered, watching in amazement as the maintenance robot painted with increasing fluency. Each stroke became more confident, more alive. The canvas bloomed with colors that spoke of longing, of discovering beauty in unexpected places.

[■■■■■■■■■■] 100% - Story complete!

As the sun set through the museum windows, UNIT-7 stepped back from its creation—a swirling galaxy of emotions in paint. In that moment, the line between artificial and authentic blurred completely.

The robot had learned to paint, but more importantly, it had learned to feel.

═══════════════════════════════════════════

✨ **Story Complete!** Would you like me to continue with UNIT-7's artistic journey, or explore a different creative prompt?
```

### Technical Explanation Stream
```
👤 You: Explain how blockchain technology works

🤖 Agent: 🔗 Breaking down blockchain technology...

[🔄 Analyzing] Organizing complex concepts for clear explanation...

═══════════════════════════════════════════

# Understanding Blockchain Technology

## 🏗️ **Foundation Concepts**

Think of blockchain as a **digital ledger** that's simultaneously stored on thousands of computers worldwide. Unlike traditional databases controlled by one organization...

[■□□□□□□□□□] 10% - Foundation laid...

Each "block" contains:
- **Transaction data** (who sent what to whom)
- **Timestamp** (when it happened)
- **Hash** (a unique digital fingerprint)
- **Previous block's hash** (linking to the chain)

[■■■□□□□□□□] 30% - Core structure explained...

## 🔐 **Security Through Cryptography**

Here's where it gets fascinating: each block's hash is calculated using the previous block's hash. This creates an unbreakable chain because...

[■■■■□□□□□□] 40% - Security model clarifying...

If someone tries to alter Block #100, its hash changes. But Block #101 expects the original hash of Block #100. The mismatch is immediately detected by the network!

[■■■■■■□□□□] 60% - Immutability principle established...

## 🌐 **Decentralized Consensus**

No single authority controls the blockchain. Instead, thousands of computers (nodes) each maintain a complete copy. When new transactions occur:

1. **Broadcasting**: Transaction announced to network
2. **Validation**: Multiple nodes verify legitimacy
3. **Mining/Consensus**: Network agrees on new block
4. **Addition**: Block added to all copies simultaneously

[■■■■■■■■□□] 80% - Consensus mechanism complete...

## 💡 **Real-World Applications**

Beyond cryptocurrency, blockchain enables:
- **Supply chain tracking** (follow food from farm to table)
- **Digital identity** (secure, user-controlled credentials)
- **Smart contracts** (self-executing agreements)
- **Voting systems** (transparent, tamper-proof elections)

[■■■■■■■■■■] 100% - Complete overview delivered!

═══════════════════════════════════════════

🎯 **Summary**: Blockchain = Distributed ledger + Cryptographic security + Decentralized consensus

Would you like me to dive deeper into any specific aspect, such as mining algorithms, smart contracts, or particular blockchain implementations?
```

## Streaming UX Patterns

### Progress Indicators
```python
# Entity automatically shows progress for long responses:
[🔄 Thinking...] → [■□□□□□□□□□] 10% → [■■■■■□□□□□] 50% → [✅ Complete!]
```

### Section Streaming
```python
# Responses are broken into logical sections:
"## Introduction" → stream content → "## Main Points" → stream content → "## Conclusion"
```

### Typing Simulation
```python
# Natural typing rhythm with varied speeds:
# - Faster for simple words
# - Slower for complex concepts
# - Pauses at punctuation
# - Hesitation before difficult topics
```

## Advanced Streaming Features

### Interactive Streaming
```yaml
streaming:
  interactive: true
  allow_interruption: true    # User can stop or redirect
  show_alternatives: true     # Offer different approaches mid-stream
  progressive_disclosure: true # Reveal complexity gradually
```

### Adaptive Streaming
```yaml
streaming:
  adaptive_speed: true        # Adjust based on user reading speed
  complexity_aware: true      # Slower for complex topics
  context_sensitive: true     # Match user's urgency level
```

### Multi-Modal Streaming
```yaml
streaming:
  text: true                  # Stream text responses
  code: true                  # Stream code with syntax highlighting
  data: true                  # Stream data analysis results
  visualizations: false       # Requires additional setup
```

## Performance Considerations

### Optimal Streaming Settings
```yaml
streaming:
  chunk_size: 50             # Balance responsiveness vs. efficiency
  delay_ms: 50               # Comfortable reading pace
  buffer_sentences: true     # Maintain readability
  max_concurrent_streams: 5   # Prevent resource overload
```

### User Experience Tuning
```yaml
streaming:
  anticipatory_start: true    # Begin streaming before complete thought
  graceful_degradation: true  # Fall back to non-streaming if issues
  bandwidth_adaptive: true    # Adjust for connection quality
```

## Running the Example

```bash
cd examples/05_streaming_responses
pip install -r requirements.txt
python streaming_agent.py
```

## Key Benefits

### ⚡ **Immediate Engagement**
- Users see responses start immediately
- No waiting for complete generation
- Maintains attention throughout response

### 🎯 **Better User Experience**
- Natural conversation flow
- Progress feedback for long responses
- Ability to interrupt or redirect

### 📊 **Performance Advantages**
- Lower perceived latency
- Better resource utilization
- Improved scalability

### 🔄 **Interactive Possibilities**
- Real-time collaboration
- Progressive refinement
- Dynamic content adjustment

## Next Steps

1. **Try the streaming agent**: Experience real-time responses
2. **Experiment with settings**: Adjust speed and chunk sizes
3. **Build interactive features**: Add interruption and redirection
4. **Explore advanced patterns**: Multi-modal and adaptive streaming

## Key Concepts Learned

✅ **Streaming Responses** for immediate user feedback
✅ **Progress Indicators** to manage user expectations
✅ **Async Response Handling** for better performance
✅ **User Experience Optimization** through streaming UX
✅ **Interactive Response Control** for dynamic conversations

---

**🎉 Congratulations!** You've completed the beginner example suite! You now understand all the core Entity Framework concepts and are ready to build sophisticated AI agents.

## 🎓 **What You've Learned**

Through these 5 examples, you've mastered:

1. **🤖 Agent Fundamentals** - Zero-config setup and basic interaction
2. **🎭 Personality Customization** - YAML-driven behavior configuration
3. **🔧 Tool Integration** - Extending agent capabilities with built-in and custom tools
4. **🧠 Memory Systems** - Persistent context and relationship building
5. **⚡ Streaming Responses** - Real-time, engaging user experiences

## 🚀 **Ready for More?**

**Intermediate Examples:**
- **[Customer Service Bot](../customer_service/)** - Real-world business application
- **[Research Assistant](../research_assistant/)** - Complex multi-tool workflows
- **[Code Reviewer](../code_reviewer/)** - Specialized domain expertise

**Advanced Examples:**
- **[Multi-Agent Systems](../multi_agent/)** - Orchestrated agent collaboration
- **[Production Deployment](../production/)** - Scalable, monitored systems
- **[Custom Plugin Development](../plugin_development/)** - Extending Entity framework

*← Previous: [Conversation Memory](../04_conversation_memory/) | Next: [Intermediate Examples](../../README.md#intermediate-examples) →*
