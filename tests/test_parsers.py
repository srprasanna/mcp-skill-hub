"""
Tests for skill parsers.

Tests cover:
- YAML frontmatter parsing
- Content extraction
- Metadata handling
- Error cases
- Folder structure validation
"""

from pathlib import Path

import pytest

from mcp_skills.parsers.base import SkillParser
from mcp_skills.parsers.markdown import MarkdownSkillParser


class TestMarkdownParserBasics:
    """Tests for basic Markdown parser functionality."""

    def test_parse_valid_skill(self, valid_skill_folder: Path) -> None:
        """Test parsing a valid skill file."""
        parser = MarkdownSkillParser(valid_skill_folder.parent)
        skill_file = valid_skill_folder / "SKILL.md"

        skill = parser.parse(skill_file)

        assert skill is not None
        assert skill.name == "test-skill"
        assert skill.description == "A test skill for unit testing"
        assert skill.version == "1.0.0"

    def test_parse_skill_with_examples(self, skill_with_examples: Path) -> None:
        """Test parsing a skill with example files."""
        parser = MarkdownSkillParser(skill_with_examples.parent)
        skill_file = skill_with_examples / "SKILL.md"

        skill = parser.parse(skill_file)

        assert skill is not None
        assert skill.has_examples is True
        assert len(skill.example_files) == 2
        assert "examples/example1.py" in skill.example_files

    def test_validate_frontmatter_format(
        self, sample_yaml_frontmatter: str
    ) -> None:
        """Test frontmatter format validation."""
        parser = MarkdownSkillParser(Path("/tmp"))

        is_valid = parser.validate(sample_yaml_frontmatter)

        assert is_valid is True

    def test_validate_rejects_invalid_format(self) -> None:
        """Test that invalid frontmatter is rejected."""
        parser = MarkdownSkillParser(Path("/tmp"))

        # Missing frontmatter delimiters
        invalid_content = "name: test\ndescription: test"

        is_valid = parser.validate(invalid_content)

        assert is_valid is False

    def test_parse_extracts_content_without_frontmatter(
        self, valid_skill_folder: Path
    ) -> None:
        """Test that content excludes frontmatter."""
        parser = MarkdownSkillParser(valid_skill_folder.parent)
        skill_file = valid_skill_folder / "SKILL.md"

        skill = parser.parse(skill_file)

        assert skill is not None
        # Content should not include frontmatter
        assert "---" not in skill.content
        assert "# Test Skill" in skill.content


class TestMarkdownParserFieldHandling:
    """Tests for handling various metadata fields."""

    def test_parse_handles_missing_optional_fields(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test parsing with only required fields."""
        # Create minimal skill
        skill_folder = tmp_skills_dir / "minimal-skill"
        skill_folder.mkdir()

        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(
            """---
name: "minimal"
description: "Minimal skill"
---

# Minimal
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is not None
        assert skill.name == "minimal"
        assert skill.description == "Minimal skill"
        assert skill.version == "1.0.0"  # Default value
        assert skill.tags == []  # Default empty list

    def test_parse_fails_without_required_name(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that parsing fails without required 'name' field."""
        skill_folder = tmp_skills_dir / "no-name-skill"
        skill_folder.mkdir()

        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(
            """---
description: "No name"
---

# Content
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is None

    def test_parse_fails_without_required_description(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that parsing fails without required 'description' field."""
        skill_folder = tmp_skills_dir / "no-desc-skill"
        skill_folder.mkdir()

        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(
            """---
name: "no-description"
---

# Content
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is None

    def test_parse_handles_complex_metadata(self, tmp_skills_dir: Path) -> None:
        """Test parsing with all metadata fields."""
        skill_folder = tmp_skills_dir / "complex-skill"
        skill_folder.mkdir()

        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(
            """---
name: "complex-skill"
description: "Complex skill with all fields"
version: "2.1.0"
author: "Test Author"
created: "2025-01-01"
updated: "2025-10-23"
dependencies:
  python: ["package1>=1.0.0", "package2"]
  system: ["git", "curl"]
category: "testing"
tags: ["test", "complex", "metadata"]
complexity: "advanced"
when_to_use:
  - "Use case 1"
  - "Use case 2"
related_skills: ["related1", "related2"]
has_examples: false
---

# Complex Skill

Full metadata example.
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is not None
        assert skill.name == "complex-skill"
        assert skill.version == "2.1.0"
        assert skill.author == "Test Author"
        assert skill.complexity == "advanced"
        assert "test" in skill.tags
        assert len(skill.when_to_use) == 2


class TestMarkdownParserDependencies:
    """Tests for dependency parsing."""

    def test_parse_flat_dependencies(self, tmp_skills_dir: Path) -> None:
        """Test parsing flat dependency list."""
        skill_folder = tmp_skills_dir / "skill"
        skill_folder.mkdir()

        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(
            """---
name: "test"
description: "Test"
dependencies: ["package1", "package2", "tool1"]
---

# Test
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is not None
        assert "package1" in skill.dependencies
        assert "package2" in skill.dependencies
        assert "tool1" in skill.dependencies

    def test_parse_nested_dependencies(self, tmp_skills_dir: Path) -> None:
        """Test parsing nested dependency dictionary."""
        skill_folder = tmp_skills_dir / "skill"
        skill_folder.mkdir()

        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(
            """---
name: "test"
description: "Test"
dependencies:
  python: ["numpy", "pandas"]
  system: ["git"]
---

# Test
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is not None
        assert "python:numpy" in skill.dependencies
        assert "python:pandas" in skill.dependencies
        assert "system:git" in skill.dependencies


class TestMarkdownParserErrorHandling:
    """Tests for error handling in parser."""

    def test_parse_invalid_yaml(self, tmp_skills_dir: Path) -> None:
        """Test parsing file with invalid YAML."""
        skill_folder = tmp_skills_dir / "invalid-yaml"
        skill_folder.mkdir()

        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(
            """---
name: "invalid
description: Missing quote
  bad indentation
---

# Content
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is None

    def test_parse_missing_frontmatter(self, tmp_skills_dir: Path) -> None:
        """Test parsing file without frontmatter."""
        skill_folder = tmp_skills_dir / "no-frontmatter"
        skill_folder.mkdir()

        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text("# Just markdown content, no frontmatter")

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is None

    def test_parse_nonexistent_file(self, tmp_skills_dir: Path) -> None:
        """Test parsing nonexistent file."""
        skill_file = tmp_skills_dir / "nonexistent" / "SKILL.md"

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is None

    def test_parse_rejects_invalid_folder_structure(
        self, tmp_skills_dir: Path, invalid_skill_in_root: Path
    ) -> None:
        """Test that parser rejects SKILL.md in root directory."""
        parser = MarkdownSkillParser(tmp_skills_dir)

        skill = parser.parse(invalid_skill_in_root)

        assert skill is None


class TestBaseParserValidation:
    """Tests for base parser folder structure validation."""

    def test_validate_folder_structure_accepts_valid(
        self, valid_skill_folder: Path
    ) -> None:
        """Test that valid folder structure is accepted."""
        skill_file = valid_skill_folder / "SKILL.md"
        parser = MarkdownSkillParser(valid_skill_folder.parent)

        is_valid, error = parser.validate_folder_structure(skill_file)

        assert is_valid is True
        assert error is None

    def test_validate_folder_structure_rejects_root_file(
        self, tmp_skills_dir: Path, invalid_skill_in_root: Path
    ) -> None:
        """Test that SKILL.md in root is rejected."""
        parser = MarkdownSkillParser(tmp_skills_dir)

        is_valid, error = parser.validate_folder_structure(invalid_skill_in_root)

        assert is_valid is False
        assert error is not None
        assert "root" in error.lower()

    def test_validate_folder_structure_rejects_hidden_folder(
        self, tmp_skills_dir: Path, hidden_skill_folder: Path
    ) -> None:
        """Test that hidden folders are rejected."""
        skill_file = hidden_skill_folder / "SKILL.md"
        parser = MarkdownSkillParser(tmp_skills_dir)

        is_valid, error = parser.validate_folder_structure(skill_file)

        assert is_valid is False
        assert error is not None
        assert "hidden" in error.lower()

    def test_validate_folder_structure_rejects_system_folder(
        self, tmp_skills_dir: Path, system_folder: Path
    ) -> None:
        """Test that system folders are rejected."""
        skill_file = system_folder / "SKILL.md"
        parser = MarkdownSkillParser(tmp_skills_dir)

        is_valid, error = parser.validate_folder_structure(skill_file)

        assert is_valid is False
        assert error is not None

    def test_validate_folder_structure_rejects_nested_skill(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that deeply nested skills are rejected."""
        # Create nested structure
        nested_folder = tmp_skills_dir / "level1" / "level2" / "skill"
        nested_folder.mkdir(parents=True)
        skill_file = nested_folder / "SKILL.md"
        skill_file.write_text("content")

        parser = MarkdownSkillParser(tmp_skills_dir)

        is_valid, error = parser.validate_folder_structure(skill_file)

        assert is_valid is False
        assert error is not None
        assert "direct child" in error.lower() or "depth" in error.lower()

    def test_validate_folder_structure_checks_filename(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that non-SKILL.md files are rejected."""
        skill_folder = tmp_skills_dir / "skill"
        skill_folder.mkdir()
        wrong_file = skill_folder / "README.md"
        wrong_file.write_text("content")

        parser = MarkdownSkillParser(tmp_skills_dir)

        is_valid, error = parser.validate_folder_structure(wrong_file)

        assert is_valid is False
        assert error is not None
        assert "SKILL.md" in error


class TestMarkdownParserIntegration:
    """Integration tests for markdown parser."""

    def test_parse_example_minimal_skill(self, tmp_skills_dir: Path) -> None:
        """Test parsing the minimal example skill format."""
        skill_folder = tmp_skills_dir / "minimal"
        skill_folder.mkdir()

        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(
            """---
name: "minimal"
description: "Minimal example"
---

# Minimal Skill

This is minimal.
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is not None
        assert skill.name == "minimal"
        assert "Minimal Skill" in skill.content

    def test_parse_example_with_examples(self, tmp_skills_dir: Path) -> None:
        """Test parsing skill with examples subdirectory."""
        skill_folder = tmp_skills_dir / "with-examples"
        skill_folder.mkdir()

        # Create examples directory
        examples_dir = skill_folder / "examples"
        examples_dir.mkdir()
        (examples_dir / "demo.py").write_text("print('hello')")

        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(
            """---
name: "with-examples"
description: "Skill with examples"
has_examples: true
example_files: ["examples/demo.py"]
---

# Skill with Examples
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        skill = parser.parse(skill_file)

        assert skill is not None
        assert skill.has_examples is True

        # Validate example files exist
        is_valid, errors = skill.validate_skill()
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
