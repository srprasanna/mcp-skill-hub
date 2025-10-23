"""
Skill repository for storage and retrieval.

This module implements the Repository pattern for managing skills in memory.
All skills stored here are guaranteed to follow proper folder structure.
"""

import logging
from typing import Optional

from mcp_skills.models.skill import Skill

logger = logging.getLogger(__name__)


class SkillRepository:
    """
    Repository for storing and retrieving skills.

    This class provides a centralized interface for skill management with
    search and filtering capabilities. All skills are stored in memory
    and validated to ensure proper folder structure.

    **Thread Safety**: This implementation is NOT thread-safe. For multi-threaded
    environments, consider adding locks or using async-safe alternatives.

    Example:
        >>> repo = SkillRepository()
        >>> repo.add(skill)
        >>> skill = repo.get("excel-advanced")
        >>> all_skills = repo.get_all()
        >>> results = repo.search(query="excel")
    """

    def __init__(self) -> None:
        """Initialize an empty skill repository."""
        self._skills: dict[str, Skill] = {}
        logger.debug("Initialized empty SkillRepository")

    def add(self, skill: Skill) -> None:
        """
        Add or update a skill in the repository.

        If a skill with the same name exists, it will be replaced.
        The skill is validated before being added.

        Args:
            skill: Skill object to add

        Raises:
            ValueError: If skill validation fails

        Example:
            >>> repo.add(skill)
            >>> print(f"Repository now has {repo.count()} skills")
        """
        # Validate skill before adding
        is_valid, errors = skill.validate_skill()
        if not is_valid:
            error_msg = (
                f"Cannot add invalid skill '{skill.name}' from folder '{skill.folder_path.name}':\n"
                + "\n".join(f"  - {err}" for err in errors)
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Add or update
        if skill.name in self._skills:
            logger.info(
                f"Updating skill '{skill.name}' in repository "
                f"(folder: {skill.folder_path.name})"
            )
        else:
            logger.info(
                f"Adding skill '{skill.name}' to repository "
                f"(folder: {skill.folder_path.name})"
            )

        self._skills[skill.name] = skill

    def remove(self, name: str) -> None:
        """
        Remove a skill from the repository by name.

        Args:
            name: Skill name to remove

        Example:
            >>> repo.remove("excel-advanced")
            >>> assert repo.get("excel-advanced") is None
        """
        if name in self._skills:
            folder_name = self._skills[name].folder_path.name
            del self._skills[name]
            logger.info(
                f"Removed skill '{name}' from repository (folder: {folder_name})"
            )
        else:
            logger.warning(f"Attempted to remove non-existent skill '{name}'")

    def get(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name.

        Args:
            name: Skill name to retrieve

        Returns:
            Skill object if found, None otherwise

        Example:
            >>> skill = repo.get("excel-advanced")
            >>> if skill:
            ...     print(f"Found: {skill.description}")
        """
        return self._skills.get(name)

    def get_all(self) -> list[Skill]:
        """
        Get all skills in the repository.

        Returns:
            List of all skill objects, sorted by name

        Example:
            >>> skills = repo.get_all()
            >>> for skill in skills:
            ...     print(f"- {skill.name}: {skill.description}")
        """
        return sorted(self._skills.values(), key=lambda s: s.name)

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        complexity: Optional[str] = None,
    ) -> list[Skill]:
        """
        Search for skills matching criteria.

        All criteria are combined with AND logic. Search is case-insensitive.

        Args:
            query: Search in name and description
            category: Filter by exact category match
            tag: Filter by tag (must be in tags list)
            complexity: Filter by complexity level

        Returns:
            List of matching skills, sorted by name

        Example:
            >>> # Search by query
            >>> results = repo.search(query="excel")
            >>> # Search by category
            >>> results = repo.search(category="data-analysis")
            >>> # Combine multiple criteria
            >>> results = repo.search(query="excel", complexity="intermediate")
        """
        results = list(self._skills.values())

        # Filter by query (search in name and description)
        if query:
            query_lower = query.lower()
            results = [
                s
                for s in results
                if query_lower in s.name.lower() or query_lower in s.description.lower()
            ]

        # Filter by category
        if category:
            results = [s for s in results if s.category == category]

        # Filter by tag
        if tag:
            results = [s for s in results if tag in s.tags]

        # Filter by complexity
        if complexity:
            results = [s for s in results if s.complexity == complexity]

        logger.debug(
            f"Search returned {len(results)} results "
            f"(query={query}, category={category}, tag={tag}, complexity={complexity})"
        )

        return sorted(results, key=lambda s: s.name)

    def clear(self) -> None:
        """
        Clear all skills from the repository.

        Example:
            >>> repo.clear()
            >>> assert repo.count() == 0
        """
        skill_count = len(self._skills)
        self._skills.clear()
        logger.info(f"Cleared repository ({skill_count} skills removed)")

    def count(self) -> int:
        """
        Get the number of skills in the repository.

        Returns:
            Number of skills

        Example:
            >>> print(f"Repository contains {repo.count()} skills")
        """
        return len(self._skills)

    def group_by_category(self) -> dict[str, list[str]]:
        """
        Group skills by category.

        Returns:
            Dictionary mapping category names to lists of skill names.
            Skills without a category are grouped under "uncategorized".

        Example:
            >>> categories = repo.group_by_category()
            >>> for cat, skills in categories.items():
            ...     print(f"{cat}: {', '.join(skills)}")
            data-analysis: pandas-tips, excel-advanced
            document-creation: docx-forms, pdf-tools
        """
        groups: dict[str, list[str]] = {}

        for skill in self._skills.values():
            category = skill.category or "uncategorized"
            if category not in groups:
                groups[category] = []
            groups[category].append(skill.name)

        # Sort skill names within each category
        for category in groups:
            groups[category].sort()

        return groups

    def get_by_folder(self, folder_name: str) -> Optional[Skill]:
        """
        Get a skill by its folder name.

        Args:
            folder_name: Name of the skill's folder (e.g., "excel-advanced")

        Returns:
            Skill object if found, None otherwise

        Example:
            >>> skill = repo.get_by_folder("excel-advanced")
            >>> if skill:
            ...     print(f"Found skill: {skill.name}")
        """
        for skill in self._skills.values():
            if skill.folder_path.name == folder_name:
                return skill
        return None

    def __len__(self) -> int:
        """Get number of skills (allows len(repo))."""
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        """Check if skill exists (allows 'name in repo')."""
        return name in self._skills

    def __repr__(self) -> str:
        """String representation."""
        return f"SkillRepository(skills={len(self._skills)})"
