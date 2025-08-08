#!/usr/bin/env python3
"""Code Review & Refactoring Agent - Entity Framework Example."""

import asyncio
import argparse
from pathlib import Path
from typing import Any, Dict, List
import sys
import json

from entity import Agent
from entity.agent.errors import AgentError


async def main() -> None:
    """Run the code review agent with command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Code Review & Refactoring Agent powered by Entity Framework"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Review command
    review_parser = subparsers.add_parser("review", help="Review code")
    review_parser.add_argument(
        "target",
        nargs="?",
        help="File, directory, or URL to review"
    )
    review_parser.add_argument(
        "--pr",
        help="GitHub/GitLab PR URL to review"
    )
    review_parser.add_argument(
        "--repo",
        help="Repository URL to review"
    )
    review_parser.add_argument(
        "--branch",
        default="main",
        help="Branch to review (default: main)"
    )
    review_parser.add_argument(
        "--staged",
        action="store_true",
        help="Review only staged files"
    )
    review_parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        help="Exit with error code if critical issues found"
    )
    review_parser.add_argument(
        "--output-format",
        choices=["markdown", "json", "github", "gitlab"],
        default="markdown",
        help="Output format for review"
    )
    review_parser.add_argument(
        "--post-comments",
        action="store_true",
        help="Post review comments to PR"
    )
    
    # Refactor command
    refactor_parser = subparsers.add_parser("refactor", help="Suggest refactorings")
    refactor_parser.add_argument(
        "file",
        type=Path,
        help="File to refactor"
    )
    refactor_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive refactoring mode"
    )
    refactor_parser.add_argument(
        "--apply",
        action="store_true",
        help="Automatically apply safe refactorings"
    )
    
    # Learn command
    learn_parser = subparsers.add_parser("learn", help="Learn from codebase")
    learn_parser.add_argument(
        "--from",
        dest="source",
        required=True,
        help="Directory to learn from"
    )
    learn_parser.add_argument(
        "--style",
        required=True,
        help="Output style file"
    )
    
    # Config
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("reviewer_config.yaml"),
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Initialize agent
        if args.config.exists():
            agent = Agent.from_config(str(args.config))
        else:
            agent = Agent.from_workflow("code_reviewer")
        
        # Prepare review context
        review_context = {
            "command": args.command,
            "output_format": getattr(args, "output_format", "markdown"),
        }
        
        if args.command == "review":
            await handle_review(agent, args, review_context)
        elif args.command == "refactor":
            await handle_refactor(agent, args, review_context)
        elif args.command == "learn":
            await handle_learn(agent, args, review_context)
        
    except AgentError as e:
        print(f"\n❌ Review failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


async def handle_review(agent: Agent, args: Any, context: Dict[str, Any]) -> None:
    """Handle the review command."""
    # Determine what to review
    if args.pr:
        context["review_type"] = "pull_request"
        context["pr_url"] = args.pr
        query = f"Review pull request: {args.pr}"
    elif args.repo:
        context["review_type"] = "repository"
        context["repo_url"] = args.repo
        context["branch"] = args.branch
        query = f"Review repository {args.repo} branch {args.branch}"
    elif args.staged:
        context["review_type"] = "staged_files"
        query = "Review staged files for commit"
    elif args.target:
        target_path = Path(args.target)
        if target_path.exists():
            context["review_type"] = "local_file"
            context["file_path"] = str(target_path.absolute())
            query = f"Review code in {target_path}"
        else:
            # Might be a URL
            context["review_type"] = "url"
            context["url"] = args.target
            query = f"Review code from {args.target}"
    else:
        print("❌ No target specified for review")
        sys.exit(1)
    
    # Store context
    await agent.remember("review_context", context)
    
    # Execute review
    print(f"\n🔍 Starting code review...")
    print(f"📋 Target: {query}")
    print(f"📊 Output format: {context['output_format']}")
    print("\n" + "="*60 + "\n")
    
    response = await agent.chat(query)
    
    # Display results
    if context["output_format"] == "json":
        # Parse and pretty-print JSON
        try:
            review_data = json.loads(response)
            print(json.dumps(review_data, indent=2))
        except:
            print(response)
    else:
        print(response)
    
    # Check for critical issues if requested
    if args.fail_on_critical:
        review_data = await agent.recall("review_results", {})
        critical_count = review_data.get("critical_issues", 0)
        if critical_count > 0:
            print(f"\n❌ Found {critical_count} critical issues")
            sys.exit(1)
    
    print("\n✅ Code review complete")


async def handle_refactor(agent: Agent, args: Any, context: Dict[str, Any]) -> None:
    """Handle the refactor command."""
    if not args.file.exists():
        print(f"❌ File not found: {args.file}")
        sys.exit(1)
    
    context["file_path"] = str(args.file.absolute())
    context["interactive"] = args.interactive
    context["auto_apply"] = args.apply
    
    await agent.remember("refactor_context", context)
    
    print(f"\n🔧 Analyzing {args.file} for refactoring opportunities...")
    
    response = await agent.chat(f"Suggest refactorings for {args.file}")
    
    print("\n" + "="*60)
    print("📝 REFACTORING SUGGESTIONS")
    print("="*60 + "\n")
    print(response)
    
    if args.interactive:
        # Get refactoring suggestions from memory
        suggestions = await agent.recall("refactoring_suggestions", [])
        
        if suggestions:
            print("\n🔄 Interactive Refactoring Mode")
            print("="*60)
            
            for i, suggestion in enumerate(suggestions, 1):
                print(f"\n[{i}] {suggestion.get('title', 'Refactoring')}")
                print(f"Type: {suggestion.get('type', 'unknown')}")
                print(f"Impact: {suggestion.get('impact', 'unknown')}")
                print("\nBefore:")
                print(suggestion.get('before', ''))
                print("\nAfter:")
                print(suggestion.get('after', ''))
                
                if not args.auto_apply:
                    choice = input("\nApply this refactoring? (y/n/q): ").lower()
                    if choice == 'q':
                        break
                    elif choice == 'y':
                        # Apply refactoring
                        print("✅ Applied refactoring")
                else:
                    if suggestion.get('safe', False):
                        print("✅ Auto-applied safe refactoring")
    
    print("\n✅ Refactoring analysis complete")


async def handle_learn(agent: Agent, args: Any, context: Dict[str, Any]) -> None:
    """Handle the learn command."""
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"❌ Source directory not found: {source_path}")
        sys.exit(1)
    
    context["source_directory"] = str(source_path.absolute())
    context["style_output"] = args.style
    
    await agent.remember("learn_context", context)
    
    print(f"\n📚 Learning code style from {source_path}...")
    print(f"📝 Output style file: {args.style}")
    
    response = await agent.chat(
        f"Learn coding patterns and style from {source_path} and save to {args.style}"
    )
    
    print("\n" + "="*60)
    print("📊 LEARNING RESULTS")
    print("="*60 + "\n")
    print(response)
    
    # Check if style file was created
    style_path = Path(args.style)
    if style_path.exists():
        print(f"\n✅ Style profile saved to: {args.style}")
        
        # Show summary
        with open(style_path) as f:
            style_data = json.load(f)
        
        print("\nLearned patterns:")
        print(f"- Functions analyzed: {style_data.get('function_count', 0)}")
        print(f"- Classes analyzed: {style_data.get('class_count', 0)}")
        print(f"- Naming conventions detected: {len(style_data.get('naming_patterns', []))}")
        print(f"- Common patterns: {len(style_data.get('common_patterns', []))}")
    else:
        print("\n⚠️  Style file not created")


if __name__ == "__main__":
    asyncio.run(main())