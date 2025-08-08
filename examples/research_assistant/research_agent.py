#!/usr/bin/env python3
"""Multi-Modal Research Assistant - Entity Framework Example."""

import asyncio
import argparse
from pathlib import Path
from typing import Any

from entity import Agent
from entity.agent.errors import AgentError


async def main() -> None:
    """Run the research assistant with command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Modal Research Assistant powered by Entity Framework"
    )
    parser.add_argument("query", help="Research query or topic")
    parser.add_argument(
        "--pdf", 
        type=Path, 
        help="PDF file to analyze alongside the query"
    )
    parser.add_argument(
        "--sources",
        default="arxiv,web",
        help="Comma-separated list of sources (arxiv,pubmed,web,semantic_scholar)"
    )
    parser.add_argument(
        "--output-format",
        choices=["academic", "executive", "blog"],
        default="academic",
        help="Output format for the research report"
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=20,
        help="Maximum number of papers to analyze"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("research_config.yaml"),
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Prepare research context
    research_context = {
        "query": args.query,
        "sources": args.sources.split(","),
        "output_format": args.output_format,
        "max_papers": args.max_papers,
    }
    
    if args.pdf and args.pdf.exists():
        research_context["pdf_path"] = str(args.pdf)
    
    try:
        # Initialize agent from configuration
        if args.config.exists():
            agent = Agent.from_config(str(args.config))
        else:
            # Use default research workflow
            agent = Agent.from_workflow("research_assistant")
        
        # Store research context in memory for plugins to access
        await agent.remember("research_context", research_context)
        
        # Start research conversation
        print(f"\n🔬 Starting research on: {args.query}")
        print(f"📚 Sources: {args.sources}")
        print(f"📊 Max papers: {args.max_papers}")
        if args.pdf:
            print(f"📄 Analyzing PDF: {args.pdf.name}")
        print("\n" + "="*60 + "\n")
        
        # Execute research
        response = await agent.chat(args.query)
        
        # Display results
        print("\n" + "="*60)
        print("📝 RESEARCH REPORT")
        print("="*60 + "\n")
        print(response)
        
        # Save report to file
        output_file = Path(f"research_report_{args.output_format}.md")
        output_file.write_text(response)
        print(f"\n✅ Report saved to: {output_file}")
        
    except AgentError as e:
        print(f"\n❌ Research failed: {e}")
        return
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())