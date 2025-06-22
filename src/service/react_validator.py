# Updated src/service/react_validator.py - Fixed for your template

import logging
import re
from typing import List, Set, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from src.core.config import EntityConfig

logger = logging.getLogger(__name__)
console = Console()


class ReActPromptValidator:
    """Validates that a prompt template is compatible with ReAct agent execution"""

    # Required variables for ReAct agent
    REQUIRED_VARIABLES = {"input", "tools", "tool_names", "agent_scratchpad"}

    # Optional but recommended variables
    OPTIONAL_VARIABLES = {"memory_context", "chat_history"}

    # ReAct format patterns that should be present
    REACT_PATTERNS = [
        r"Thought:",
        r"Action:",
        r"Action Input:",
        r"Observation:",
        r"Final Answer:",
    ]

    # Strict formatting requirements (updated to be more flexible)
    STRICT_FORMAT_REQUIREMENTS = [
        {
            "pattern": r"Action.*MUST.*tool name|Action.*ONLY.*tool|Action.*exact",
            "description": "Action line formatting rules",
            "severity": "warning",
        },
        {
            "pattern": r"Action Input.*own line|Action Input.*next line",
            "description": "Action Input formatting rules",
            "severity": "warning",
        },
        {
            "pattern": r"CORRECT.*EXAMPLE|✅.*CORRECT|EXAMPLE.*Action:",
            "description": "Examples of correct format",
            "severity": "info",
        },
        {
            "pattern": r"WRONG.*EXAMPLE|❌.*WRONG|DO NOT USE|NEVER.*Action",
            "description": "Examples showing wrong format",
            "severity": "info",
        },
    ]

    # Updated problematic patterns - more specific to avoid false positives
    PROBLEMATIC_PATTERNS = [
        {
            "pattern": r"Action:\s*\w+\s*\([^)]*\)\s*$",  # Only match if it's the complete line
            "description": "Action with parenthetical description at end of line",
            "example": "Action: memory_search (searching for memories)",
            "fix": "Action: memory_search\nAction Input: searching for memories",
            "severity": "error",
        },
        {
            "pattern": r"Action:\s*\w+\s*-[^\\n]*$",  # Only match if it's the complete line
            "description": "Action with dash description at end of line",
            "example": "Action: memory_search - looking for past conversations",
            "fix": "Action: memory_search\nAction Input: looking for past conversations",
            "severity": "error",
        },
    ]

    @classmethod
    def validate_on_startup(
        cls, config: EntityConfig, show_success: bool = True
    ) -> bool:
        """
        Comprehensive validation shown in terminal on startup
        Returns True if validation passes, False otherwise
        """
        console.print("\n" + "=" * 60)
        console.print(
            "[bold cyan]🔍 ReAct Prompt Template Validation[/bold cyan]",
            justify="center",
        )
        console.print("=" * 60 + "\n")

        prompt_template = config.prompts.base_prompt
        declared_variables = set(config.prompts.variables)

        validation_passed = True
        issues_found = []

        # 1. Check required variables
        missing_required = cls.REQUIRED_VARIABLES - declared_variables
        if missing_required:
            validation_passed = False
            issues_found.append(
                {
                    "type": "error",
                    "category": "Required Variables",
                    "message": f"Missing required variables: {', '.join(missing_required)}",
                    "fix": f"Add to config.yml prompts.variables: {list(missing_required)}",
                }
            )
        else:
            if show_success:
                console.print("✅ [green]All required variables present[/green]")

        # 2. Check variable usage consistency
        template_variables = cls._extract_template_variables(prompt_template)
        undeclared_vars = template_variables - declared_variables
        unused_vars = declared_variables - template_variables

        if undeclared_vars:
            validation_passed = False
            issues_found.append(
                {
                    "type": "error",
                    "category": "Variable Declaration",
                    "message": f"Template uses undeclared variables: {', '.join(undeclared_vars)}",
                    "fix": f"Add to config.yml prompts.variables: {list(undeclared_vars)}",
                }
            )

        if unused_vars:
            issues_found.append(
                {
                    "type": "warning",
                    "category": "Variable Usage",
                    "message": f"Declared but unused variables: {', '.join(unused_vars)}",
                    "fix": "Remove from config.yml or use in template",
                }
            )

        # 3. Check ReAct format patterns
        missing_patterns = []
        for pattern in cls.REACT_PATTERNS:
            if not re.search(pattern, prompt_template, re.IGNORECASE):
                missing_patterns.append(pattern)

        if missing_patterns:
            validation_passed = False
            issues_found.append(
                {
                    "type": "error",
                    "category": "ReAct Format",
                    "message": f"Missing ReAct patterns: {', '.join(missing_patterns)}",
                    "fix": "Add missing patterns to your prompt template",
                }
            )
        else:
            if show_success:
                console.print("✅ [green]All ReAct format patterns found[/green]")

        # 4. Check for strict formatting guidance (updated to be more flexible)
        format_guidance_score = 0
        for req in cls.STRICT_FORMAT_REQUIREMENTS:
            if re.search(req["pattern"], prompt_template, re.IGNORECASE):
                format_guidance_score += 1

        if format_guidance_score >= 1:  # Lowered requirement from 2 to 1
            if show_success:
                console.print("✅ [green]Good formatting guidance provided[/green]")
        else:
            issues_found.append(
                {
                    "type": "warning",
                    "category": "Format Guidance",
                    "message": "Prompt lacks strict formatting instructions for LLM",
                    "fix": "Add explicit rules about Action/Action Input format",
                }
            )

        # 5. Check for problematic patterns (updated to be more specific)
        for problem in cls.PROBLEMATIC_PATTERNS:
            # Split prompt into lines and check each line individually
            lines = prompt_template.split("\n")
            found_problematic = False

            for line in lines:
                # Skip lines that are clearly examples showing wrong format
                if any(
                    marker in line.upper()
                    for marker in ["WRONG", "DO NOT", "❌", "NEVER"]
                ):
                    continue

                if re.search(problem["pattern"], line.strip()):
                    found_problematic = True
                    break

            if found_problematic:
                validation_passed = False
                issues_found.append(
                    {
                        "type": "error",
                        "category": "Parsing Issues",
                        "message": problem["description"],
                        "example": problem["example"],
                        "fix": problem["fix"],
                        "severity": problem["severity"],
                    }
                )

        # 6. Check agent_scratchpad placement
        if "{agent_scratchpad}" not in prompt_template:
            validation_passed = False
            issues_found.append(
                {
                    "type": "error",
                    "category": "Template Structure",
                    "message": "{agent_scratchpad} variable missing from template",
                    "fix": "Add {agent_scratchpad} at the end of your prompt",
                }
            )

        # Display results
        if validation_passed and not issues_found:
            cls._display_success()
        else:
            cls._display_issues(issues_found, validation_passed)

        # Show prompt snippet
        cls._display_prompt_snippet(prompt_template)

        console.print("\n" + "=" * 60 + "\n")

        return validation_passed

    @classmethod
    def _display_success(cls):
        """Display success message"""
        success_panel = Panel(
            "[bold green]✅ ReAct Prompt Validation PASSED[/bold green]\n\n"
            "Your prompt template is properly configured for ReAct agent execution.",
            title="✅ Validation Success",
            border_style="green",
        )
        console.print(success_panel)

    @classmethod
    def _display_issues(cls, issues: List[Dict], validation_passed: bool):
        """Display validation issues in a structured format"""

        # Overall status
        if validation_passed:
            status_text = "[yellow]⚠️ WARNINGS FOUND[/yellow]"
            status_color = "yellow"
        else:
            status_text = "[red]❌ VALIDATION FAILED[/red]"
            status_color = "red"

        console.print(f"\n{status_text}\n")

        # Group issues by type
        errors = [i for i in issues if i["type"] == "error"]
        warnings = [i for i in issues if i["type"] == "warning"]

        # Display errors
        if errors:
            console.print("[bold red]🚨 Critical Issues (Must Fix):[/bold red]")
            error_table = Table(show_header=True, header_style="bold red")
            error_table.add_column("Category", style="red", width=20)
            error_table.add_column("Issue", style="white", width=40)
            error_table.add_column("Fix", style="cyan", width=35)

            for error in errors:
                error_table.add_row(
                    error["category"],
                    error["message"],
                    error.get("fix", "See documentation"),
                )
            console.print(error_table)
            console.print()

        # Display warnings
        if warnings:
            console.print("[bold yellow]⚠️ Warnings (Recommended):[/bold yellow]")
            warning_table = Table(show_header=True, header_style="bold yellow")
            warning_table.add_column("Category", style="yellow", width=20)
            warning_table.add_column("Issue", style="white", width=40)
            warning_table.add_column("Fix", style="cyan", width=35)

            for warning in warnings:
                warning_table.add_row(
                    warning["category"],
                    warning["message"],
                    warning.get("fix", "See documentation"),
                )
            console.print(warning_table)
            console.print()

        # Show examples for parsing issues
        parsing_issues = [i for i in issues if i["category"] == "Parsing Issues"]
        if parsing_issues:
            console.print("[bold red]📝 Common Parsing Problems:[/bold red]")
            for issue in parsing_issues:
                if "example" in issue:
                    console.print(f"[red]❌ Wrong:[/red] {issue['example']}")
                    console.print(f"[green]✅ Right:[/green] {issue['fix']}")
                    console.print()

    @classmethod
    def _display_prompt_snippet(cls, prompt: str):
        """Display a snippet of the current prompt"""
        console.print(prompt.strip(), style="dim")

    @classmethod
    def validate_prompt(cls, config: EntityConfig) -> bool:
        """Original validation method (kept for backwards compatibility)"""
        return cls.validate_on_startup(config, show_success=False)

    @classmethod
    def _extract_template_variables(cls, template: str) -> Set[str]:
        """Extract all {variable} placeholders from template"""
        pattern = r"\{([^}]+)\}"
        variables = set(re.findall(pattern, template))
        return variables

    @classmethod
    def get_validation_report(cls, config: EntityConfig) -> dict:
        """Get detailed validation report (kept for CLI command)"""
        prompt_template = config.prompts.base_prompt
        declared_variables = set(config.prompts.variables)
        template_variables = cls._extract_template_variables(prompt_template)

        report = {
            "is_valid": cls.validate_prompt(config),
            "required_variables": {
                "present": cls.REQUIRED_VARIABLES.intersection(declared_variables),
                "missing": cls.REQUIRED_VARIABLES - declared_variables,
            },
            "optional_variables": {
                "present": cls.OPTIONAL_VARIABLES.intersection(declared_variables),
                "missing": cls.OPTIONAL_VARIABLES - declared_variables,
            },
            "template_variables": {
                "declared": declared_variables,
                "used_in_template": template_variables,
                "undeclared": template_variables - declared_variables,
                "unused": declared_variables - template_variables,
            },
            "react_patterns": {
                "found": [
                    p
                    for p in cls.REACT_PATTERNS
                    if re.search(p, prompt_template, re.IGNORECASE)
                ],
                "missing": [
                    p
                    for p in cls.REACT_PATTERNS
                    if not re.search(p, prompt_template, re.IGNORECASE)
                ],
            },
        }

        return report

    @classmethod
    def suggest_fixes(cls, config: EntityConfig) -> List[str]:
        """Suggest fixes for prompt validation issues"""
        suggestions = []
        report = cls.get_validation_report(config)

        if report["required_variables"]["missing"]:
            suggestions.append(
                f"Add missing required variables to config.prompts.variables: {list(report['required_variables']['missing'])}"
            )

        if report["template_variables"]["undeclared"]:
            suggestions.append(
                f"Add undeclared variables to config.prompts.variables: {list(report['template_variables']['undeclared'])}"
            )

        if report["react_patterns"]["missing"]:
            suggestions.append(
                f"Add missing ReAct patterns to your prompt: {report['react_patterns']['missing']}"
            )

        if not report["is_valid"]:
            suggestions.append(
                "Consider using a standard ReAct prompt template that includes proper Thought/Action/Observation structure"
            )

        return suggestions
