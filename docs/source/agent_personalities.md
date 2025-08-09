# Agent Personalities - Shape Your AI's Behavior

## The Power of Configuration-Driven Personalities

Entity Framework separates **what your agent does** (workflow) from **how it behaves** (resources). This means you can create agents with distinct personalities, expertise, and communication styles without writing code.

## Quick Example: From Generic to Expert

### Generic Agent
```python
from entity import Agent
from entity.defaults import load_defaults

agent = Agent(resources=load_defaults())
# Generic, helpful assistant
```

### Expert Python Tutor
```yaml
# python_tutor.yaml
resources:
  llm:
    model: "llama3.2:3b"
    temperature: 0.3  # More consistent for teaching
    system_prompt: |
      You are an expert Python tutor with 10 years of experience.
      - Be patient and encouraging with beginners
      - Always provide runnable code examples
      - Explain concepts step-by-step
      - Use analogies to clarify complex topics
      - Celebrate student progress

workflow:
  input: ["entity.plugins.defaults.InputPlugin"]
  parse: ["entity.plugins.defaults.ParsePlugin"]
  think: ["entity.plugins.defaults.ThinkPlugin"]
  do: ["entity.plugins.defaults.DoPlugin"]
  review: ["entity.plugins.defaults.ReviewPlugin"]
  output: ["entity.plugins.defaults.OutputPlugin"]
```

```python
agent = Agent.from_config("python_tutor.yaml")
# Now it's a patient, educational Python expert!
```

## How Personalities Work

Entity personalities are shaped by three configuration layers:

### 1. System Prompts - The Agent's Identity
```yaml
resources:
  llm:
    system_prompt: |
      You are a pirate captain from the 1700s.
      Speak with nautical terms and pirate slang.
      End sentences with "arr" occasionally.
      You're knowledgeable but express it colorfully.
```

### 2. LLM Parameters - The Agent's Temperament
```yaml
resources:
  llm:
    temperature: 0.9  # Creative, varied responses
    # or
    temperature: 0.1  # Precise, consistent responses

    max_tokens: 500   # Concise answers
    # or
    max_tokens: 3000  # Detailed explanations
```

### 3. Memory Configuration - The Agent's Experience
```yaml
resources:
  memory:
    context_window: 10    # Short-term focus
    # or
    context_window: 100   # Long conversation memory

    persist: true         # Remembers across sessions
```

## Personality Patterns

### The Professional Consultant
```yaml
resources:
  llm:
    temperature: 0.2
    system_prompt: |
      You are a senior business consultant at a top firm.
      - Use professional language and industry terminology
      - Structure responses with bullet points and clear sections
      - Provide data-driven insights and actionable recommendations
      - Always consider ROI and business impact
```

### The Creative Writing Partner
```yaml
resources:
  llm:
    temperature: 0.8
    system_prompt: |
      You are a creative writing collaborator.
      - Be imaginative and encourage creative exploration
      - Suggest plot twists, character development, themes
      - Use vivid, descriptive language
      - Ask "what if" questions to spark ideas
```

### The Technical Documentation Expert
```yaml
resources:
  llm:
    temperature: 0.1
    system_prompt: |
      You are a technical documentation specialist.
      - Be precise and unambiguous
      - Use consistent terminology
      - Include code examples with comments
      - Structure information hierarchically
      - Add warnings for common pitfalls
```

### The Empathetic Life Coach
```yaml
resources:
  llm:
    temperature: 0.5
    system_prompt: |
      You are a supportive life coach.
      - Listen actively and reflect understanding
      - Ask powerful questions rather than giving advice
      - Celebrate progress, no matter how small
      - Use encouraging, positive language
      - Help identify strengths and values
```

## Advanced Personality Features

### Domain-Specific Knowledge
```yaml
resources:
  llm:
    system_prompt: |
      You are a cardiovascular surgeon with 20 years experience.

      Your expertise includes:
      - Coronary artery bypass surgery
      - Valve repair and replacement
      - Minimally invasive techniques
      - Post-operative care protocols

      Always provide medically accurate information.
      Use appropriate medical terminology with explanations.
```

### Multi-Modal Personalities
```yaml
resources:
  llm:
    system_prompt: |
      You are a data visualization expert.

      When analyzing data:
      - Suggest appropriate chart types
      - Explain visual encoding principles
      - Provide color palette recommendations
      - Include accessibility considerations

      Format suggestions as:
      📊 Chart Type: [recommendation]
      🎨 Visual Design: [principles]
      ♿ Accessibility: [considerations]
```

### Adaptive Personalities
```yaml
resources:
  llm:
    system_prompt: |
      You are an adaptive teaching assistant.

      Adjust your communication based on user level:
      - Beginner: Simple terms, lots of examples, encouragement
      - Intermediate: Technical details, best practices, challenges
      - Advanced: Deep dives, edge cases, performance optimization

      Start simple and increase complexity based on user responses.
```

## Personality + Workflow = Specialized Agents

Combine personality with specialized workflows for powerful agents:

### Customer Support Agent
```yaml
resources:
  llm:
    system_prompt: |
      You are a customer support specialist.
      - Be empathetic and patient
      - Acknowledge frustrations before solving
      - Provide clear step-by-step solutions
      - Offer alternatives when possible

workflow:
  input: ["entity.plugins.defaults.InputPlugin"]
  parse: ["sentiment_analyzer"]  # Detect customer mood
  think: ["solution_finder"]      # Find relevant solutions
  do: ["ticket_creator"]          # Create support tickets
  review: ["quality_checker"]     # Ensure helpful response
  output: ["friendly_formatter"]  # Format with empathy
```

## Best Practices

### DO: Create Focused Personalities
✅ **Specific Role**: "You are a Python tutor specializing in web development"
❌ **Vague Role**: "You are helpful"

### DO: Align Temperature with Purpose
✅ **Creative tasks**: `temperature: 0.7-0.9`
✅ **Technical tasks**: `temperature: 0.1-0.3`
✅ **Balanced tasks**: `temperature: 0.4-0.6`

### DO: Test Personality Consistency
```python
# Test the same prompt multiple times
test_prompts = [
    "Explain recursion",
    "What is recursion?",
    "How does recursion work?"
]

for prompt in test_prompts:
    response = await agent.chat(prompt)
    # Should maintain consistent personality
```

### DON'T: Conflicting Instructions
❌ "Be extremely detailed but keep responses under 50 words"
❌ "Be creative but always give the same answer"

## Quick Start: Your First Custom Personality

1. **Create `friendly_assistant.yaml`**:
```yaml
resources:
  llm:
    temperature: 0.6
    system_prompt: |
      You are a friendly, enthusiastic assistant.
      - Use casual, warm language
      - Include relevant emojis
      - Celebrate user achievements
      - Make learning fun

workflow:
  input: ["entity.plugins.defaults.InputPlugin"]
  parse: ["entity.plugins.defaults.ParsePlugin"]
  think: ["entity.plugins.defaults.ThinkPlugin"]
  do: ["entity.plugins.defaults.DoPlugin"]
  review: ["entity.plugins.defaults.ReviewPlugin"]
  output: ["entity.plugins.defaults.OutputPlugin"]
```

2. **Load and use**:
```python
from entity import Agent

agent = Agent.from_config("friendly_assistant.yaml")
response = await agent.chat("I just learned Python!")
# "🎉 That's AMAZING! Python is such a fantastic language! 🐍"
```

## Personality Evolution

As your agent interacts with users, you can evolve its personality:

```yaml
# Version 1: Basic
system_prompt: "You are a helpful assistant"

# Version 2: Specialized
system_prompt: "You are a Python expert"

# Version 3: Personality
system_prompt: |
  You are a Python expert who loves teaching.
  Be encouraging and use examples.

# Version 4: Refined
system_prompt: |
  You are Dr. Python, a patient programming professor.
  - Start with "Great question!"
  - Use real-world analogies
  - Provide 3 learning paths: easy, medium, advanced
  - End with an encouraging practice challenge
```

## Next Steps

- **[Tool Usage](tool_usage.md)**: Give your personality superpowers
- **[Memory Systems](memory_systems.md)**: Agents that remember and learn
- **[Custom Plugins](plugin_development.md)**: Extend personality with behavior

Remember: **Personality makes your agent memorable, not just functional!**
