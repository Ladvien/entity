#!/usr/bin/env python3
"""Entity Framework Showcase - Complete feature demonstration.

This example showcases EVERY major feature of Entity Framework:
- Multi-modal input processing (text, files, images, voice, URLs)
- Advanced reasoning with context synthesis
- Powerful tool integration (search, visualization, file ops)
- Quality assurance with fact-checking and safety filters
- Flexible output (reports, dashboards, notifications)
- Production-ready monitoring and logging

This is the "Swiss Army Knife" of AI agents, demonstrating why Entity
Framework is the fastest way to build production-ready AI applications.

Usage:
    python showcase_agent.py

Then try commands like:
- "analyze sales_data.csv and create a dashboard"
- "research quantum computing trends and write a report"
- "describe this image: photo.jpg"
- "review the security of this Python script"
"""

import asyncio
from pathlib import Path

from entity import Agent


def print_banner():
    """Display the showcase banner with example commands."""
    print("🌟" * 50)
    print("🎯 Entity Framework Complete Showcase")
    print("🌟" * 50)
    print()
    print("This agent demonstrates EVERY Entity Framework feature:")
    print("• Multi-modal input (text, files, images, voice, URLs)")
    print("• Advanced reasoning and context synthesis")
    print("• Powerful tools (search, analysis, visualization)")
    print("• Quality assurance (fact-checking, safety)")
    print("• Flexible output (reports, dashboards, exports)")
    print()
    print("🎮 Try these example commands:")
    print()
    print("📊 DATA ANALYSIS:")
    print("  > analyze data.csv and create visualizations")
    print("  > find trends in our quarterly sales data")
    print()
    print("🔍 RESEARCH & REPORTS:")
    print("  > research AI trends 2024 and write an executive summary")
    print("  > fact-check this article: https://example.com/news")
    print()
    print("🖼️ IMAGE & MEDIA:")
    print("  > describe this image: photo.jpg")
    print("  > transcribe and summarize: meeting_audio.mp3")
    print()
    print("💻 CODE & DEVELOPMENT:")
    print("  > review the security of this Python script: app.py")
    print("  > optimize this SQL query for better performance")
    print()
    print("📧 COMMUNICATION:")
    print("  > draft professional email about Q4 results")
    print("  > create presentation slides about our new product")
    print()
    print("🎓 EDUCATION & EXPLANATION:")
    print("  > explain machine learning like I'm 12 years old")
    print("  > create a tutorial on React hooks with examples")
    print()
    print("🌐 WEB & CONTENT:")
    print("  > summarize the latest tech news from Hacker News")
    print("  > create a competitive analysis of our industry")
    print()
    print("📈 BUSINESS INTELLIGENCE:")
    print("  > analyze our customer feedback and find insights")
    print("  > predict next quarter's sales based on current data")
    print()
    print("=" * 60)
    print("Type your request or '/help' for more commands...")
    print("=" * 60)


async def main():
    """Run the Entity Framework showcase agent."""

    # Configuration path
    config_path = Path(__file__).parent / "showcase_config.yaml"

    # Check if config exists
    if not config_path.exists():
        print("⚠️  Configuration file not found!")
        print(f"Expected: {config_path}")
        print()
        print("This showcase requires a complete configuration file.")
        print("For now, falling back to a simplified demo...")
        print()

        # Use default agent for demonstration
        try:
            from entity.defaults import load_defaults

            resources = load_defaults()
            agent = Agent(resources=resources)

            print("✅ Demo agent loaded with default configuration")
            print("📝 Note: Full showcase features require showcase_config.yaml")
            print()
            print("🎮 You can still try basic commands like:")
            print("  > Hello, tell me about Entity Framework")
            print("  > What can you help me with?")
            print("  > Explain the benefits of plugin architecture")
            print()

        except Exception as e:
            print(f"❌ Failed to load demo agent: {e}")
            print()
            print("To run the full showcase:")
            print("1. Ensure entity-core is installed: pip install entity-core")
            print("2. Configure your LLM provider (Ollama recommended)")
            print("3. Create showcase_config.yaml with plugin definitions")
            return

    else:
        try:
            # Load the full showcase agent
            agent = Agent.from_config(str(config_path))
            print("🚀 Full Entity Framework Showcase loaded!")
            print("✅ All plugins active and ready")
            print()

        except Exception as e:
            print(f"❌ Error loading showcase configuration: {e}")
            print("Falling back to basic demo mode...")

            try:
                from entity.defaults import load_defaults

                resources = load_defaults()
                agent = Agent(resources=resources)
                print("✅ Demo mode active")

            except Exception as e2:
                print(f"❌ Complete failure: {e2}")
                return

    # Display banner and examples
    print_banner()

    try:
        # Start interactive session
        # Empty string triggers Entity's interactive mode
        await agent.chat("")

    except KeyboardInterrupt:
        print()
        print("👋 Thanks for trying the Entity Framework Showcase!")
        print("🌟 Ready to build your own production AI agents?")
        print("📚 Learn more: https://github.com/your-repo/entity-framework")

    except Exception as e:
        print(f"\n❌ Showcase error: {e}")
        print()
        print("🔧 Troubleshooting tips:")
        print("• Check that Ollama is running (or API keys set)")
        print("• Verify all dependencies are installed")
        print("• Try the simpler examples first (simple_chat/)")
        print("• Check Entity documentation for setup help")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        print()
        print("Entity Framework Showcase")
        print("Demonstrates the complete power of plugin-based AI development")
        print()
        print("For simpler examples, try:")
        print("• examples/simple_chat/ - Basic conversational agent")
        print("• examples/code_reviewer/ - Specialized code analysis")
        print("• examples/default_agent.py - Minimal Entity usage")
