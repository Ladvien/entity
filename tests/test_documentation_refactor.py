"""Test that refactored documentation maintains essential information."""

import os
import re


def test_readme_files_exist():
    """Verify main README files exist."""
    assert os.path.exists("/Users/ladvien/entity/README.md")
    assert os.path.exists("/Users/ladvien/entity/examples/README.md")
    assert os.path.exists("/Users/ladvien/entity/plugins/template/README.md")


def test_readme_word_count_reduced():
    """Verify README files have been significantly reduced."""
    # Original word counts
    original_counts = {"main": 1829, "examples": 487, "template": 878}

    # Get current word counts
    with open("/Users/ladvien/entity/README.md") as f:
        main_words = len(f.read().split())

    with open("/Users/ladvien/entity/examples/README.md") as f:
        examples_words = len(f.read().split())

    with open("/Users/ladvien/entity/plugins/template/README.md") as f:
        template_words = len(f.read().split())

    # Verify at least 50% reduction
    assert (
        main_words < original_counts["main"] * 0.5
    ), f"Main README not reduced enough: {main_words} words"
    assert (
        examples_words < original_counts["examples"] * 0.5
    ), f"Examples README not reduced enough: {examples_words} words"
    assert (
        template_words < original_counts["template"] * 0.5
    ), f"Template README not reduced enough: {template_words} words"


def test_essential_sections_present():
    """Verify essential sections are still present in main README."""
    with open("/Users/ladvien/entity/README.md") as f:
        content = f.read()

    # Check for essential sections
    assert "## Quick Start" in content or "Quick Start" in content
    assert (
        "## Installation" in content
        or "Installation" in content
        or "pip install" in content
    )
    assert "## Progressive Examples" in content or "Examples" in content
    assert "## Architecture" in content or "Pipeline" in content or "6-Stage" in content


def test_code_examples_present():
    """Verify README files contain executable code examples."""
    with open("/Users/ladvien/entity/README.md") as f:
        main_content = f.read()

    with open("/Users/ladvien/entity/examples/README.md") as f:
        examples_content = f.read()

    # Check for code blocks
    assert "```python" in main_content, "Main README missing Python code examples"
    assert "```bash" in main_content, "Main README missing bash examples"
    assert (
        "from entity import Agent" in main_content
    ), "Main README missing import examples"
    assert "await agent.chat" in main_content, "Main README missing usage examples"

    assert "```python" in examples_content, "Examples README missing Python code"
    assert "from entity" in examples_content, "Examples README missing imports"


def test_concise_descriptions():
    """Verify descriptions are concise and direct."""
    with open("/Users/ladvien/entity/README.md") as f:
        content = f.read()

    # Check that we're not using verbose phrases
    verbose_phrases = [
        "it is important to note that",
        "please be aware that",
        "it should be mentioned",
        "as you can see",
        "basically what this does",
        "in order to",
        "for the purpose of",
    ]

    content_lower = content.lower()
    for phrase in verbose_phrases:
        assert phrase not in content_lower, f"Found verbose phrase: {phrase}"


def test_progressive_disclosure():
    """Verify progressive disclosure pattern - simple first, complex later."""
    with open("/Users/ladvien/entity/README.md") as f:
        content = f.read()

    # Find code examples
    code_blocks = re.findall(r"```python(.*?)```", content, re.DOTALL)

    if len(code_blocks) >= 2:
        # First example should be simpler (fewer lines) than later ones
        first_lines = len(code_blocks[0].strip().split("\n"))

        # At least one later example should be more complex
        has_complex = any(
            len(block.strip().split("\n")) > first_lines for block in code_blocks[1:]
        )
        assert (
            has_complex or first_lines <= 5
        ), "Examples don't follow progressive disclosure"


def test_encouraging_but_direct():
    """Verify tone is encouraging but direct."""
    with open("/Users/ladvien/entity/README.md") as f:
        content = f.read()

    # Should have some encouraging elements
    encouraging_indicators = ["🚀", "✅", "Quick Start", "minutes", "fast", "simple"]
    has_encouraging = any(indicator in content for indicator in encouraging_indicators)
    assert has_encouraging, "README lacks encouraging tone"

    # But should be direct (short sentences, action-oriented)
    lines = content.split("\n")
    non_empty_lines = [l for l in lines if l.strip() and not l.startswith("#")]
    if non_empty_lines:
        # Check average line length (should be concise)
        avg_length = sum(len(l) for l in non_empty_lines) / len(non_empty_lines)
        assert avg_length < 100, f"Lines too long on average: {avg_length:.1f} chars"


def test_no_redundant_content():
    """Verify no redundant explanations across documents."""
    with open("/Users/ladvien/entity/README.md") as f:
        main_content = f.read()

    with open("/Users/ladvien/entity/examples/README.md") as f:
        examples_content = f.read()

    # Extract substantial text blocks (more than 50 chars)
    def extract_blocks(text):
        lines = text.split("\n")
        blocks = []
        for line in lines:
            if (
                len(line) > 50
                and not line.startswith("#")
                and not line.startswith("```")
            ):
                blocks.append(line.strip())
        return blocks

    main_blocks = extract_blocks(main_content)
    examples_blocks = extract_blocks(examples_content)

    # Check for duplicate content
    duplicates = set(main_blocks) & set(examples_blocks)

    # Allow some minimal overlap but not too much
    assert (
        len(duplicates) < 3
    ), f"Too much duplicate content between READMEs: {duplicates}"
