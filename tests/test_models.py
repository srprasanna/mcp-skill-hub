"""
Tests for the Skill model.

Tests cover:
- Model creation and validation
- Field validators
- Methods (uri, to_dict, validate_skill, get_example_path)
- Error cases
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from mcp_skills.models.skill import Skill


class TestSkillModelCreation:
    """Tests for creating Skill instances."""

    def test_create_minimal_skill(self, tmp_path: Path) -> None:
        """Test creating a skill with only required fields."""
        folder = tmp_path / "test-skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="test-skill",
            description="Test description",
            content="Test content",
            path=skill_file,
            folder_path=folder,
        )

        assert skill.name == "test-skill"
        assert skill.description == "Test description"
        assert skill.content == "Test content"
        assert skill.version == "1.0.0"  # Default
        assert skill.tags == []  # Default
        assert skill.has_examples is False  # Default

    def test_create_skill_with_all_fields(self, tmp_path: Path) -> None:
        """Test creating a skill with all metadata fields."""
        folder = tmp_path / "complex-skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="complex-skill",
            description="Complex skill",
            content="Content here",
            path=skill_file,
            folder_path=folder,
            version="2.1.0",
            author="Test Author",
            created="2025-01-01",
            updated="2025-10-23",
            dependencies=["python:numpy", "system:git"],
            tags=["test", "complex"],
            category="testing",
            complexity="advanced",
            when_to_use=["Use case 1", "Use case 2"],
            related_skills=["other-skill"],
            has_examples=True,
            example_files=["examples/test.py"],
        )

        assert skill.name == "complex-skill"
        assert skill.version == "2.1.0"
        assert skill.author == "Test Author"
        assert skill.complexity == "advanced"
        assert "test" in skill.tags
        assert skill.category == "testing"
        assert len(skill.when_to_use) == 2
        assert skill.has_examples is True

    def test_name_validation_strips_whitespace(self, tmp_path: Path) -> None:
        """Test that skill names are stripped of whitespace."""
        folder = tmp_path / "skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="  test-skill  ",
            description="Test",
            content="Content",
            path=skill_file,
            folder_path=folder,
        )

        assert skill.name == "test-skill"

    def test_empty_name_raises_error(self, tmp_path: Path) -> None:
        """Test that empty name raises ValidationError."""
        folder = tmp_path / "skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        with pytest.raises(ValidationError) as exc_info:
            Skill(
                name="   ",
                description="Test",
                content="Content",
                path=skill_file,
                folder_path=folder,
            )

        assert "name cannot be empty" in str(exc_info.value).lower()

    def test_invalid_complexity_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid complexity level raises ValidationError."""
        folder = tmp_path / "skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        with pytest.raises(ValidationError) as exc_info:
            Skill(
                name="test",
                description="Test",
                content="Content",
                path=skill_file,
                folder_path=folder,
                complexity="expert",  # Invalid
            )

        assert "complexity" in str(exc_info.value).lower()


class TestSkillMethods:
    """Tests for Skill model methods."""

    def test_uri_method(self, tmp_path: Path) -> None:
        """Test the uri() method."""
        folder = tmp_path / "test-skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="test-skill",
            description="Test",
            content="Content",
            path=skill_file,
            folder_path=folder,
        )

        assert skill.uri() == "skill://test-skill"

    def test_to_dict_method(self, tmp_path: Path) -> None:
        """Test the to_dict() method."""
        folder = tmp_path / "test-skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="test-skill",
            description="Test description",
            content="Content",
            path=skill_file,
            folder_path=folder,
            tags=["test"],
        )

        data = skill.to_dict()

        assert data["name"] == "test-skill"
        assert data["description"] == "Test description"
        assert data["uri"] == "skill://test-skill"
        assert isinstance(data["path"], str)
        assert isinstance(data["folder_path"], str)
        assert "test" in data["tags"]

    def test_get_example_path(self, tmp_path: Path) -> None:
        """Test the get_example_path() method."""
        folder = tmp_path / "test-skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="test-skill",
            description="Test",
            content="Content",
            path=skill_file,
            folder_path=folder,
        )

        example_path = skill.get_example_path("examples/demo.py")

        assert example_path == folder / "examples" / "demo.py"

    def test_validate_skill_success(self, valid_skill_folder: Path) -> None:
        """Test validate_skill() with valid skill."""
        skill_file = valid_skill_folder / "SKILL.md"

        skill = Skill(
            name="test-skill",
            description="Test",
            content="Content",
            path=skill_file,
            folder_path=valid_skill_folder,
        )

        is_valid, errors = skill.validate_skill()

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_skill_detects_missing_file(self, tmp_path: Path) -> None:
        """Test validate_skill() detects missing SKILL.md file."""
        folder = tmp_path / "skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"  # Not created

        skill = Skill(
            name="test",
            description="Test",
            content="Content",
            path=skill_file,
            folder_path=folder,
        )

        is_valid, errors = skill.validate_skill()

        assert is_valid is False
        assert any("not found" in err.lower() for err in errors)

    def test_validate_skill_detects_invalid_folder_structure(
        self, tmp_path: Path
    ) -> None:
        """Test validate_skill() detects invalid folder structure."""
        folder = tmp_path / "skill"
        folder.mkdir()

        # SKILL.md in wrong location (not directly in folder)
        subfolder = folder / "subfolder"
        subfolder.mkdir()
        skill_file = subfolder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="test",
            description="Test",
            content="Content",
            path=skill_file,
            folder_path=folder,
        )

        is_valid, errors = skill.validate_skill()

        assert is_valid is False
        assert any("folder structure" in err.lower() for err in errors)

    def test_validate_skill_detects_missing_example_files(
        self, tmp_path: Path
    ) -> None:
        """Test validate_skill() detects missing example files."""
        folder = tmp_path / "skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="test",
            description="Test",
            content="Content",
            path=skill_file,
            folder_path=folder,
            has_examples=True,
            example_files=["examples/missing.py"],
        )

        is_valid, errors = skill.validate_skill()

        assert is_valid is False
        assert any("example file not found" in err.lower() for err in errors)

    def test_validate_skill_detects_has_examples_without_files(
        self, tmp_path: Path
    ) -> None:
        """Test validate_skill() detects has_examples=True with no files."""
        folder = tmp_path / "skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="test",
            description="Test",
            content="Content",
            path=skill_file,
            folder_path=folder,
            has_examples=True,
            example_files=[],
        )

        is_valid, errors = skill.validate_skill()

        assert is_valid is False
        assert any("has_examples" in err.lower() for err in errors)


class TestSkillStringRepresentation:
    """Tests for Skill string representations."""

    def test_str_representation(self, tmp_path: Path) -> None:
        """Test __str__ method."""
        folder = tmp_path / "test-skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="test-skill",
            description="Test",
            content="Content",
            path=skill_file,
            folder_path=folder,
            version="1.2.0",
        )

        str_repr = str(skill)

        assert "test-skill" in str_repr
        assert "1.2.0" in str_repr
        assert folder.name in str_repr

    def test_repr_representation(self, tmp_path: Path) -> None:
        """Test __repr__ method."""
        folder = tmp_path / "test-skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="test-skill",
            description="Test description",
            content="Content",
            path=skill_file,
            folder_path=folder,
        )

        repr_str = repr(skill)

        assert "Skill" in repr_str
        assert "test-skill" in repr_str
        assert "Test description" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
