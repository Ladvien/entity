# src/service/react_prompt_validator.py

import logging
import re
from typing import List, Set
from src.service.config import EntityConfig

logger = logging.getLogger(__name__)


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

    @classmethod
    def validate_prompt(cls, config: EntityConfig) -> bool:
        """
        Validate that the prompt template is compatible with ReAct execution

        Returns:
            bool: True if valid, False otherwise
        """
        prompt_template = config.prompts.base_prompt
        declared_variables = set(config.prompts.variables)

        logger.info("🔍 Validating ReAct prompt compatibility...")

        # Check 1: Required variables are declared
        missing_required = cls.REQUIRED_VARIABLES - declared_variables
        if missing_required:
            logger.error(f"❌ Missing required variables: {missing_required}")
            return False

        logger.info(f"✅ All required variables present: {cls.REQUIRED_VARIABLES}")

        # Check 2: Variables in template match declared variables
        template_variables = cls._extract_template_variables(prompt_template)
        undeclared_variables = template_variables - declared_variables

        if undeclared_variables:
            logger.warning(
                f"⚠️ Template uses undeclared variables: {undeclared_variables}"
            )

        unused_variables = declared_variables - template_variables
        if unused_variables:
            logger.warning(f"⚠️ Declared but unused variables: {unused_variables}")

        # Check 3: ReAct format patterns are present
        missing_patterns = []
        for pattern in cls.REACT_PATTERNS:
            if not re.search(pattern, prompt_template, re.IGNORECASE):
                missing_patterns.append(pattern)

        if missing_patterns:
            logger.warning(f"⚠️ Missing ReAct format patterns: {missing_patterns}")
            logger.warning("This may affect step-by-step reasoning display")
        else:
            logger.info("✅ All ReAct format patterns found")

        # Check 4: Essential ReAct structure
        has_thought_action = (
            "Thought:" in prompt_template
            and "Action:" in prompt_template
            and "Final Answer:" in prompt_template
        )

        if not has_thought_action:
            logger.error(
                "❌ Prompt missing essential ReAct structure (Thought/Action/Final Answer)"
            )
            return False

        logger.info("✅ Essential ReAct structure validated")

        # Check 5: agent_scratchpad placement
        if "{agent_scratchpad}" not in prompt_template:
            logger.error("❌ {agent_scratchpad} variable not found in template")
            return False

        # Should be at the end or after "Thought:"
        scratchpad_position = prompt_template.find("{agent_scratchpad}")
        if not (
            prompt_template[scratchpad_position - 10 : scratchpad_position].find(
                "Thought:"
            )
            >= 0
            or scratchpad_position > len(prompt_template) * 0.8
        ):
            logger.warning(
                "⚠️ {agent_scratchpad} should be positioned after 'Thought:' or at the end"
            )

        logger.info("✅ ReAct prompt validation completed successfully")
        return True

    @classmethod
    def _extract_template_variables(cls, template: str) -> Set[str]:
        """Extract all {variable} placeholders from template"""
        pattern = r"\{([^}]+)\}"
        variables = set(re.findall(pattern, template))
        return variables

    @classmethod
    def get_validation_report(cls, config: EntityConfig) -> dict:
        """Get detailed validation report"""
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
