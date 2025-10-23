"""
Tests for the Skill Repository.

Tests cover:
- CRUD operations
- Search functionality
- Category grouping
- Validation
"""

from pathlib import Path

import pytest

from mcp_skills.models.skill import Skill
from mcp_skills.storage.repository import SkillRepository


@pytest.fixture
def sample_skill(tmp_path: Path) -> Skill:
    """Create a sample skill for testing."""
    folder = tmp_path / "test-skill"
    folder.mkdir()
    skill_file = folder / "SKILL.md"
    skill_file.write_text("content")

    return Skill(
        name="test-skill",
        description="Test skill",
        content="Test content",
        path=skill_file,
        folder_path=folder,
        tags=["test", "sample"],
        category="testing",
        complexity="beginner",
    )


@pytest.fixture
def another_skill(tmp_path: Path) -> Skill:
    """Create another sample skill for testing."""
    folder = tmp_path / "another-skill"
    folder.mkdir()
    skill_file = folder / "SKILL.md"
    skill_file.write_text("content")

    return Skill(
        name="another-skill",
        description="Another skill",
        content="Another content",
        path=skill_file,
        folder_path=folder,
        tags=["test", "other"],
        category="other",
        complexity="intermediate",
    )


class TestRepositoryBasics:
    """Tests for basic repository operations."""

    def test_create_empty_repository(self) -> None:
        """Test creating an empty repository."""
        repo = SkillRepository()

        assert repo.count() == 0
        assert len(repo.get_all()) == 0

    def test_add_skill(self, sample_skill: Skill) -> None:
        """Test adding a skill to repository."""
        repo = SkillRepository()

        repo.add(sample_skill)

        assert repo.count() == 1
        assert "test-skill" in repo

    def test_add_multiple_skills(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test adding multiple skills."""
        repo = SkillRepository()

        repo.add(sample_skill)
        repo.add(another_skill)

        assert repo.count() == 2
        assert "test-skill" in repo
        assert "another-skill" in repo

    def test_add_skill_twice_updates(self, sample_skill: Skill) -> None:
        """Test that adding same skill twice updates it."""
        repo = SkillRepository()

        repo.add(sample_skill)
        repo.add(sample_skill)

        assert repo.count() == 1

    def test_get_skill(self, sample_skill: Skill) -> None:
        """Test getting a skill by name."""
        repo = SkillRepository()
        repo.add(sample_skill)

        retrieved = repo.get("test-skill")

        assert retrieved is not None
        assert retrieved.name == "test-skill"
        assert retrieved.description == "Test skill"

    def test_get_nonexistent_skill(self) -> None:
        """Test getting a non-existent skill returns None."""
        repo = SkillRepository()

        retrieved = repo.get("nonexistent")

        assert retrieved is None

    def test_remove_skill(self, sample_skill: Skill) -> None:
        """Test removing a skill."""
        repo = SkillRepository()
        repo.add(sample_skill)

        repo.remove("test-skill")

        assert repo.count() == 0
        assert "test-skill" not in repo

    def test_remove_nonexistent_skill(self) -> None:
        """Test removing a non-existent skill doesn't error."""
        repo = SkillRepository()

        # Should not raise an error
        repo.remove("nonexistent")

        assert repo.count() == 0

    def test_clear_repository(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test clearing all skills."""
        repo = SkillRepository()
        repo.add(sample_skill)
        repo.add(another_skill)

        repo.clear()

        assert repo.count() == 0
        assert len(repo.get_all()) == 0


class TestRepositoryGetAll:
    """Tests for getting all skills."""

    def test_get_all_empty(self) -> None:
        """Test get_all on empty repository."""
        repo = SkillRepository()

        all_skills = repo.get_all()

        assert len(all_skills) == 0

    def test_get_all_returns_sorted(
        self, sample_skill: Skill, another_skill: Skill, tmp_path: Path
    ) -> None:
        """Test get_all returns skills sorted by name."""
        repo = SkillRepository()

        # Add in reverse alphabetical order
        folder = tmp_path / "zebra-skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        zebra_skill = Skill(
            name="zebra-skill",
            description="Zebra",
            content="Content",
            path=skill_file,
            folder_path=folder,
        )

        repo.add(zebra_skill)
        repo.add(sample_skill)
        repo.add(another_skill)

        all_skills = repo.get_all()

        assert len(all_skills) == 3
        assert all_skills[0].name == "another-skill"
        assert all_skills[1].name == "test-skill"
        assert all_skills[2].name == "zebra-skill"


class TestRepositorySearch:
    """Tests for search functionality."""

    def test_search_by_query_in_name(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test searching by query matching name."""
        repo = SkillRepository()
        repo.add(sample_skill)
        repo.add(another_skill)

        results = repo.search(query="test")

        assert len(results) == 1
        assert results[0].name == "test-skill"

    def test_search_by_query_in_description(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test searching by query matching description."""
        repo = SkillRepository()
        repo.add(sample_skill)
        repo.add(another_skill)

        results = repo.search(query="another")

        assert len(results) == 1
        assert results[0].name == "another-skill"

    def test_search_by_query_case_insensitive(
        self, sample_skill: Skill
    ) -> None:
        """Test search is case-insensitive."""
        repo = SkillRepository()
        repo.add(sample_skill)

        results = repo.search(query="TEST")

        assert len(results) == 1
        assert results[0].name == "test-skill"

    def test_search_by_category(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test searching by category."""
        repo = SkillRepository()
        repo.add(sample_skill)
        repo.add(another_skill)

        results = repo.search(category="testing")

        assert len(results) == 1
        assert results[0].name == "test-skill"

    def test_search_by_tag(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test searching by tag."""
        repo = SkillRepository()
        repo.add(sample_skill)
        repo.add(another_skill)

        results = repo.search(tag="other")

        assert len(results) == 1
        assert results[0].name == "another-skill"

    def test_search_by_complexity(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test searching by complexity."""
        repo = SkillRepository()
        repo.add(sample_skill)
        repo.add(another_skill)

        results = repo.search(complexity="beginner")

        assert len(results) == 1
        assert results[0].name == "test-skill"

    def test_search_multiple_criteria(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test searching with multiple criteria (AND logic)."""
        repo = SkillRepository()
        repo.add(sample_skill)
        repo.add(another_skill)

        results = repo.search(query="test", category="testing")

        assert len(results) == 1
        assert results[0].name == "test-skill"

    def test_search_no_results(self, sample_skill: Skill) -> None:
        """Test search with no matching results."""
        repo = SkillRepository()
        repo.add(sample_skill)

        results = repo.search(query="nonexistent")

        assert len(results) == 0

    def test_search_no_criteria_returns_all(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test search with no criteria returns all skills."""
        repo = SkillRepository()
        repo.add(sample_skill)
        repo.add(another_skill)

        results = repo.search()

        assert len(results) == 2


class TestRepositoryGrouping:
    """Tests for grouping functionality."""

    def test_group_by_category(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test grouping skills by category."""
        repo = SkillRepository()
        repo.add(sample_skill)
        repo.add(another_skill)

        groups = repo.group_by_category()

        assert "testing" in groups
        assert "other" in groups
        assert "test-skill" in groups["testing"]
        assert "another-skill" in groups["other"]

    def test_group_by_category_uncategorized(self, tmp_path: Path) -> None:
        """Test that skills without category go to 'uncategorized'."""
        folder = tmp_path / "uncategorized-skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        skill = Skill(
            name="uncategorized-skill",
            description="No category",
            content="Content",
            path=skill_file,
            folder_path=folder,
            category=None,
        )

        repo = SkillRepository()
        repo.add(skill)

        groups = repo.group_by_category()

        assert "uncategorized" in groups
        assert "uncategorized-skill" in groups["uncategorized"]

    def test_group_by_category_sorted(
        self, sample_skill: Skill, another_skill: Skill, tmp_path: Path
    ) -> None:
        """Test that skills within categories are sorted."""
        folder = tmp_path / "alpha-skill"
        folder.mkdir()
        skill_file = folder / "SKILL.md"
        skill_file.write_text("content")

        alpha_skill = Skill(
            name="alpha-skill",
            description="Alpha",
            content="Content",
            path=skill_file,
            folder_path=folder,
            category="testing",
        )

        repo = SkillRepository()
        repo.add(sample_skill)  # test-skill
        repo.add(alpha_skill)  # alpha-skill

        groups = repo.group_by_category()

        # Skills in category should be sorted
        assert groups["testing"][0] == "alpha-skill"
        assert groups["testing"][1] == "test-skill"


class TestRepositoryGetByFolder:
    """Tests for getting skills by folder name."""

    def test_get_by_folder_name(self, sample_skill: Skill) -> None:
        """Test getting skill by folder name."""
        repo = SkillRepository()
        repo.add(sample_skill)

        skill = repo.get_by_folder("test-skill")

        assert skill is not None
        assert skill.name == "test-skill"

    def test_get_by_folder_nonexistent(self) -> None:
        """Test getting by non-existent folder returns None."""
        repo = SkillRepository()

        skill = repo.get_by_folder("nonexistent")

        assert skill is None


class TestRepositoryMagicMethods:
    """Tests for repository magic methods."""

    def test_len_magic_method(
        self, sample_skill: Skill, another_skill: Skill
    ) -> None:
        """Test len() magic method."""
        repo = SkillRepository()
        repo.add(sample_skill)
        repo.add(another_skill)

        assert len(repo) == 2

    def test_contains_magic_method(self, sample_skill: Skill) -> None:
        """Test 'in' operator (contains)."""
        repo = SkillRepository()
        repo.add(sample_skill)

        assert "test-skill" in repo
        assert "nonexistent" not in repo

    def test_repr_method(self, sample_skill: Skill) -> None:
        """Test __repr__ method."""
        repo = SkillRepository()
        repo.add(sample_skill)

        repr_str = repr(repo)

        assert "SkillRepository" in repr_str
        assert "skills=1" in repr_str


class TestRepositoryValidation:
    """Tests for repository validation."""

    def test_add_invalid_skill_raises_error(self, tmp_path: Path) -> None:
        """Test that adding invalid skill raises error."""
        folder = tmp_path / "skill"
        folder.mkdir()
        skill_file = tmp_path / "SKILL.md"  # Not in folder!
        skill_file.write_text("content")

        skill = Skill(
            name="invalid",
            description="Invalid skill",
            content="Content",
            path=skill_file,
            folder_path=folder,
        )

        repo = SkillRepository()

        with pytest.raises(ValueError) as exc_info:
            repo.add(skill)

        assert "invalid" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
