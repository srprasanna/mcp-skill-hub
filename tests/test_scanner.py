"""
Tests for the Skill Scanner.

Tests cover:
- Directory scanning
- Folder validation
- Depth control
- Error handling
"""

from pathlib import Path

import pytest

from mcp_skills.parsers.markdown import MarkdownSkillParser
from mcp_skills.scanner import SkillScanner


class TestScannerBasics:
    """Tests for basic scanner functionality."""

    def test_scan_empty_directory(self, tmp_skills_dir: Path) -> None:
        """Test scanning an empty directory."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        assert len(skills) == 0

    def test_scan_single_valid_skill(self, valid_skill_folder: Path) -> None:
        """Test scanning directory with one valid skill."""
        skills_dir = valid_skill_folder.parent
        parser = MarkdownSkillParser(skills_dir)
        scanner = SkillScanner(skills_dir, parser)

        skills = scanner.scan()

        assert len(skills) == 1
        assert "test-skill" in skills

    def test_scan_multiple_valid_skills(
        self, valid_skill_folder: Path, skill_with_examples: Path
    ) -> None:
        """Test scanning directory with multiple valid skills."""
        skills_dir = valid_skill_folder.parent
        parser = MarkdownSkillParser(skills_dir)
        scanner = SkillScanner(skills_dir, parser)

        skills = scanner.scan()

        assert len(skills) == 2
        assert "test-skill" in skills
        assert "skill-with-examples" in skills


class TestScannerFolderValidation:
    """Tests for folder structure validation in scanner."""

    def test_is_valid_skill_folder_accepts_normal_folder(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that normal folders are valid."""
        folder = tmp_skills_dir / "normal-folder"
        folder.mkdir()

        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        assert scanner._is_valid_skill_folder(folder) is True

    def test_is_valid_skill_folder_rejects_hidden_folder(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that hidden folders are rejected."""
        folder = tmp_skills_dir / ".hidden"
        folder.mkdir()

        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        assert scanner._is_valid_skill_folder(folder) is False

    def test_is_valid_skill_folder_rejects_underscore_folder(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that folders starting with _ are rejected."""
        folder = tmp_skills_dir / "_private"
        folder.mkdir()

        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        assert scanner._is_valid_skill_folder(folder) is False

    def test_is_valid_skill_folder_rejects_system_folders(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that system folders are rejected."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        for folder_name in ["__pycache__", "node_modules", ".git", ".vscode"]:
            folder = tmp_skills_dir / folder_name
            folder.mkdir()

            assert scanner._is_valid_skill_folder(folder) is False

    def test_is_valid_skill_folder_requires_directory(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that non-directories are rejected."""
        file_path = tmp_skills_dir / "file.txt"
        file_path.write_text("content")

        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        assert scanner._is_valid_skill_folder(file_path) is False


class TestScannerSkipsInvalidStructures:
    """Tests that scanner skips invalid folder structures."""

    def test_scan_skips_root_skill_file(
        self, tmp_skills_dir: Path, invalid_skill_in_root: Path
    ) -> None:
        """Test that SKILL.md in root is skipped."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        assert len(skills) == 0

    def test_scan_skips_hidden_folders(
        self, tmp_skills_dir: Path, hidden_skill_folder: Path
    ) -> None:
        """Test that hidden folders are skipped."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        assert len(skills) == 0

    def test_scan_skips_system_folders(
        self, tmp_skills_dir: Path, system_folder: Path
    ) -> None:
        """Test that system folders are skipped."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        assert len(skills) == 0

    def test_scan_skips_folders_without_skill_file(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that folders without SKILL.md are skipped."""
        empty_folder = tmp_skills_dir / "empty-folder"
        empty_folder.mkdir()

        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        assert len(skills) == 0


class TestScannerDepthControl:
    """Tests that scanner only scans immediate subdirectories."""

    def test_scan_only_depth_one(self, tmp_skills_dir: Path) -> None:
        """Test that scanner only scans depth=1."""
        # Create valid skill at depth 1
        skill_folder = tmp_skills_dir / "valid-skill"
        skill_folder.mkdir()
        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(
            """---
name: "valid"
description: "Valid skill"
---
# Valid
"""
        )

        # Create nested skill at depth 2
        nested_folder = skill_folder / "nested-skill"
        nested_folder.mkdir()
        nested_file = nested_folder / "SKILL.md"
        nested_file.write_text(
            """---
name: "nested"
description: "Nested skill"
---
# Nested
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        # Should only find depth-1 skill
        assert len(skills) == 1
        assert "valid" in skills
        assert "nested" not in skills


class TestScannerMixedContent:
    """Tests scanner with mixed valid and invalid content."""

    def test_scan_mixed_valid_and_invalid(
        self,
        tmp_skills_dir: Path,
        valid_skill_folder: Path,
        hidden_skill_folder: Path,
        invalid_skill_in_root: Path,
    ) -> None:
        """Test scanning with mix of valid and invalid structures."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        # Should only find the valid skill
        assert len(skills) == 1
        assert "test-skill" in skills

    def test_scan_continues_after_parse_failure(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test that scanner continues after a parse failure."""
        # Create one skill with invalid YAML
        invalid_folder = tmp_skills_dir / "invalid-skill"
        invalid_folder.mkdir()
        invalid_file = invalid_folder / "SKILL.md"
        invalid_file.write_text(
            """---
name: invalid yaml
---
# Invalid
"""
        )

        # Create one valid skill
        valid_folder = tmp_skills_dir / "valid-skill"
        valid_folder.mkdir()
        valid_file = valid_folder / "SKILL.md"
        valid_file.write_text(
            """---
name: "valid"
description: "Valid skill"
---
# Valid
"""
        )

        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skills = scanner.scan()

        # Should find the valid skill despite invalid one
        assert "valid" in skills


class TestScannerHelperMethods:
    """Tests for scanner helper methods."""

    def test_find_skill_file_finds_existing(
        self, valid_skill_folder: Path
    ) -> None:
        """Test _find_skill_file finds existing SKILL.md."""
        parser = MarkdownSkillParser(valid_skill_folder.parent)
        scanner = SkillScanner(valid_skill_folder.parent, parser)

        skill_file = scanner._find_skill_file(valid_skill_folder)

        assert skill_file is not None
        assert skill_file.name == "SKILL.md"
        assert skill_file.exists()

    def test_find_skill_file_returns_none_if_missing(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test _find_skill_file returns None if no SKILL.md."""
        empty_folder = tmp_skills_dir / "empty"
        empty_folder.mkdir()

        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        skill_file = scanner._find_skill_file(empty_folder)

        assert skill_file is None

    def test_get_folder_skip_reason(self, tmp_skills_dir: Path) -> None:
        """Test _get_folder_skip_reason provides reasons."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        # Hidden folder
        hidden = tmp_skills_dir / ".hidden"
        hidden.mkdir()
        reason = scanner._get_folder_skip_reason(hidden)
        assert "hidden" in reason.lower()

        # Private folder - this one is checked first and returns "private"
        private = tmp_skills_dir / "_private"
        private.mkdir()
        reason = scanner._get_folder_skip_reason(private)
        assert "private" in reason.lower() or "_" in reason

        # System folder
        pycache = tmp_skills_dir / "__pycache__"
        pycache.mkdir()
        reason = scanner._get_folder_skip_reason(pycache)
        # __pycache__ starts with _ so may return "private" or "system"
        assert "system" in reason.lower() or "private" in reason.lower() or "pycache" in reason.lower()


class TestScannerDirectoryValidation:
    """Tests for directory structure validation."""

    def test_validate_directory_structure_succeeds(
        self, valid_skill_folder: Path
    ) -> None:
        """Test validation succeeds for valid structure."""
        skills_dir = valid_skill_folder.parent
        parser = MarkdownSkillParser(skills_dir)
        scanner = SkillScanner(skills_dir, parser)

        is_valid, issues = scanner.validate_directory_structure()

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_directory_structure_detects_missing_dir(
        self, tmp_path: Path
    ) -> None:
        """Test validation detects non-existent directory."""
        nonexistent = tmp_path / "nonexistent"
        parser = MarkdownSkillParser(nonexistent)
        scanner = SkillScanner(nonexistent, parser)

        is_valid, issues = scanner.validate_directory_structure()

        assert is_valid is False
        assert len(issues) > 0
        assert any("not exist" in issue.lower() for issue in issues)

    def test_validate_directory_structure_detects_no_valid_folders(
        self, tmp_skills_dir: Path
    ) -> None:
        """Test validation detects lack of valid skill folders."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        is_valid, issues = scanner.validate_directory_structure()

        assert is_valid is False
        assert len(issues) > 0
        assert any("no valid" in issue.lower() for issue in issues)


class TestScannerAsync:
    """Tests for async scanning."""

    @pytest.mark.asyncio
    async def test_scan_async(self, valid_skill_folder: Path) -> None:
        """Test async scanning."""
        skills_dir = valid_skill_folder.parent
        parser = MarkdownSkillParser(skills_dir)
        scanner = SkillScanner(skills_dir, parser)

        skills = await scanner.scan_async()

        assert len(skills) == 1
        assert "test-skill" in skills


class TestScannerRepr:
    """Tests for scanner string representation."""

    def test_repr(self, tmp_skills_dir: Path) -> None:
        """Test __repr__ method."""
        parser = MarkdownSkillParser(tmp_skills_dir)
        scanner = SkillScanner(tmp_skills_dir, parser)

        repr_str = repr(scanner)

        assert "SkillScanner" in repr_str
        assert str(tmp_skills_dir) in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
