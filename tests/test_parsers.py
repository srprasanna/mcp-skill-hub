"""
Tests for skill parsers.

These tests verify YAML frontmatter parsing, content extraction,
and metadata handling.
"""

from pathlib import Path

import pytest

from mcp_skills.parsers.markdown import MarkdownSkillParser


class TestMarkdownParser:
    """Tests for the Markdown skill parser."""

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
