"""
Pytest configuration and fixtures for MCP Skills Server tests.

This module provides common fixtures used across the test suite,
particularly for creating temporary skill directories with proper
folder structure.
"""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_skills_dir(tmp_path: Path) -> Path:
    """
    Create a temporary skills directory for testing.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to temporary skills directory
    """
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    return skills_dir


@pytest.fixture
def valid_skill_folder(tmp_skills_dir: Path) -> Path:
    """
    Create a valid skill folder with SKILL.md.

    Structure:
        /skills/
        └── test-skill/
            └── SKILL.md

    Args:
        tmp_skills_dir: Temporary skills directory

    Returns:
        Path to the skill folder
    """
    skill_folder = tmp_skills_dir / "test-skill"
    skill_folder.mkdir()

    skill_file = skill_folder / "SKILL.md"
    skill_file.write_text(
        """---
name: "test-skill"
description: "A test skill for unit testing"
version: "1.0.0"
---

# Test Skill

This is a test skill used in unit tests.
"""
    )

    return skill_folder


@pytest.fixture
def skill_with_examples(tmp_skills_dir: Path) -> Path:
    """
    Create a skill folder with example files.

    Structure:
        /skills/
        └── skill-with-examples/
            ├── SKILL.md
            └── examples/
                ├── example1.py
                └── example2.txt

    Args:
        tmp_skills_dir: Temporary skills directory

    Returns:
        Path to the skill folder
    """
    skill_folder = tmp_skills_dir / "skill-with-examples"
    skill_folder.mkdir()

    # Create SKILL.md
    skill_file = skill_folder / "SKILL.md"
    skill_file.write_text(
        """---
name: "skill-with-examples"
description: "Test skill with example files"
has_examples: true
example_files: ["examples/example1.py", "examples/example2.txt"]
---

# Skill With Examples

This skill includes example files.
"""
    )

    # Create examples directory
    examples_dir = skill_folder / "examples"
    examples_dir.mkdir()

    (examples_dir / "example1.py").write_text("# Example Python file\nprint('Hello')\n")
    (examples_dir / "example2.txt").write_text("Example text file content\n")

    return skill_folder


@pytest.fixture
def invalid_skill_in_root(tmp_skills_dir: Path) -> Path:
    """
    Create an invalid SKILL.md file in the root directory.

    This should be skipped by the scanner.

    Structure:
        /skills/
        └── SKILL.md  ← Invalid (not in a folder)

    Args:
        tmp_skills_dir: Temporary skills directory

    Returns:
        Path to the invalid skill file
    """
    invalid_file = tmp_skills_dir / "SKILL.md"
    invalid_file.write_text(
        """---
name: "invalid-skill"
description: "This should be skipped"
---

# Invalid Skill

This file is in the root directory and should be skipped.
"""
    )
    return invalid_file


@pytest.fixture
def hidden_skill_folder(tmp_skills_dir: Path) -> Path:
    """
    Create a hidden skill folder (should be skipped).

    Structure:
        /skills/
        └── .hidden-skill/
            └── SKILL.md

    Args:
        tmp_skills_dir: Temporary skills directory

    Returns:
        Path to the hidden skill folder
    """
    hidden_folder = tmp_skills_dir / ".hidden-skill"
    hidden_folder.mkdir()

    skill_file = hidden_folder / "SKILL.md"
    skill_file.write_text(
        """---
name: "hidden-skill"
description: "This should be skipped"
---

# Hidden Skill
"""
    )
    return hidden_folder


@pytest.fixture
def system_folder(tmp_skills_dir: Path) -> Path:
    """
    Create a system folder (should be skipped).

    Structure:
        /skills/
        └── __pycache__/
            └── SKILL.md

    Args:
        tmp_skills_dir: Temporary skills directory

    Returns:
        Path to the system folder
    """
    system_folder = tmp_skills_dir / "__pycache__"
    system_folder.mkdir()

    skill_file = system_folder / "SKILL.md"
    skill_file.write_text(
        """---
name: "system-skill"
description: "This should be skipped"
---

# System Skill
"""
    )
    return system_folder


@pytest.fixture
def sample_yaml_frontmatter() -> str:
    """
    Provide sample YAML frontmatter for testing.

    Returns:
        Valid YAML frontmatter string
    """
    return """---
name: "sample-skill"
description: "Sample skill for testing"
version: "1.0.0"
author: "Test Author"
tags: ["test", "sample"]
complexity: "beginner"
---

# Sample Skill

Sample content for testing.
"""


@pytest.fixture
def invalid_yaml_frontmatter() -> str:
    """
    Provide invalid YAML frontmatter for testing.

    Returns:
        Invalid YAML frontmatter string
    """
    return """---
name: "invalid-skill
description: Missing closing quote
  invalid indentation
---

# Invalid Skill
"""
