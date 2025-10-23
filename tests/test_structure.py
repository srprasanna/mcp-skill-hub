"""
Tests for folder structure validation.

These tests verify that the server correctly enforces the requirement
that each skill must be in its own dedicated folder.
"""

from pathlib import Path

import pytest

from mcp_skills.parsers.markdown import MarkdownSkillParser
from mcp_skills.scanner import SkillScanner


class TestFolderStructureValidation:
    """Tests for folder structure validation logic."""

    def test_skill_must_be_in_folder(
        self, tmp_skills_dir: Path, invalid_skill_in_root: Path
    ) -> None:
        """Test that SKILL.md files in root directory are rejected."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        # Scan should not find the invalid skill
        skills = scanner.scan()

        assert len(skills) == 0, "Root SKILL.md file should not be loaded"

    def test_hidden_folders_are_skipped(
        self, tmp_skills_dir: Path, hidden_skill_folder: Path
    ) -> None:
        """Test that folders starting with . are skipped."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        # Scan should skip hidden folders
        skills = scanner.scan()

        assert len(skills) == 0, "Hidden folders should be skipped"
        assert not scanner._is_valid_skill_folder(hidden_skill_folder)

    def test_ignored_folders_are_skipped(
        self, tmp_skills_dir: Path, system_folder: Path
    ) -> None:
        """Test that __pycache__, node_modules, etc. are skipped."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        # Scan should skip system folders
        skills = scanner.scan()

        assert len(skills) == 0, "System folders should be skipped"
        assert not scanner._is_valid_skill_folder(system_folder)

    def test_valid_folder_structure_is_accepted(
        self, tmp_skills_dir: Path, valid_skill_folder: Path
    ) -> None:
        """Test that properly structured skills are loaded."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        # Scan should find the valid skill
        skills = scanner.scan()

        assert len(skills) == 1, "Valid skill should be loaded"
        assert "test-skill" in skills
        assert skills["test-skill"].name == "test-skill"

    def test_skill_with_examples_loads_correctly(
        self, tmp_skills_dir: Path, skill_with_examples: Path
    ) -> None:
        """Test that skills with example subdirectories load correctly."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        # Scan should find the skill with examples
        skills = scanner.scan()

        assert len(skills) == 1
        skill = skills["skill-with-examples"]
        assert skill.has_examples
        assert len(skill.example_files) == 2
        assert "examples/example1.py" in skill.example_files

    def test_parser_validates_folder_structure(
        self, tmp_skills_dir: Path, invalid_skill_in_root: Path
    ) -> None:
        """Test that parser validates folder structure."""
        parser = MarkdownSkillParser(tmp_skills_dir)

        # Try to parse invalid file
        is_valid, error = parser.validate_folder_structure(invalid_skill_in_root)

        assert not is_valid, "Root SKILL.md should fail validation"
        assert error is not None
        assert "root" in error.lower() or "folder" in error.lower()

    def test_parser_accepts_valid_folder_structure(
        self, valid_skill_folder: Path
    ) -> None:
        """Test that parser accepts valid folder structure."""
        skill_file = valid_skill_folder / "SKILL.md"
        parser = MarkdownSkillParser(valid_skill_folder.parent)

        is_valid, error = parser.validate_folder_structure(skill_file)

        assert is_valid, f"Valid folder structure should pass: {error}"
        assert error is None


class TestScannerBehavior:
    """Tests for scanner behavior with various folder structures."""

    def test_scanner_handles_empty_directory(self, tmp_skills_dir: Path) -> None:
        """Test scanner behavior with empty skills directory."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        assert len(skills) == 0, "Empty directory should return no skills"

    def test_scanner_handles_mixed_valid_and_invalid(
        self,
        tmp_skills_dir: Path,
        valid_skill_folder: Path,
        hidden_skill_folder: Path,
        invalid_skill_in_root: Path,
    ) -> None:
        """Test scanner with mix of valid and invalid structures."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        # Should only find the valid skill
        assert len(skills) == 1
        assert "test-skill" in skills

    def test_scanner_depth_is_one(self, tmp_skills_dir: Path) -> None:
        """Test that scanner only scans immediate subdirectories."""
        # Create nested structure
        skill_folder = tmp_skills_dir / "valid-skill"
        skill_folder.mkdir()
        (skill_folder / "SKILL.md").write_text(
            """---
name: "valid"
description: "Valid skill"
---
# Valid"""
        )

        nested_folder = skill_folder / "nested-skill"
        nested_folder.mkdir()
        (nested_folder / "SKILL.md").write_text(
            """---
name: "nested"
description: "Nested skill"
---
# Nested"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        # Should only find the top-level skill, not the nested one
        assert len(skills) >= 1, "Should find at least the valid skill"
        assert "valid" in skills, "Should find the valid skill"
        assert "nested" not in skills, "Should not find nested skill"


class TestValidationMessages:
    """Tests for validation error messages."""

    def test_error_message_includes_folder_context(
        self, tmp_skills_dir: Path, invalid_skill_in_root: Path
    ) -> None:
        """Test that error messages include folder context."""
        parser = MarkdownSkillParser(tmp_skills_dir)

        is_valid, error = parser.validate_folder_structure(invalid_skill_in_root)

        assert not is_valid
        assert error is not None
        # Error should mention folder requirement
        assert any(
            keyword in error.lower()
            for keyword in ["folder", "directory", "structure"]
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
