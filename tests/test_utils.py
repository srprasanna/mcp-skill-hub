"""
Tests for utility functions.

Tests cover:
- Skill URI formatting
- JSON serialization
- Skill name validation
"""

import json
from pathlib import Path

import pytest

from mcp_skills.utils import format_skill_uri, safe_json_dumps, validate_skill_name


class TestFormatSkillUri:
    """Tests for format_skill_uri function."""

    def test_format_skill_uri(self) -> None:
        """Test formatting skill name to URI."""
        uri = format_skill_uri("test-skill")

        assert uri == "skill://test-skill"

    def test_format_skill_uri_with_special_chars(self) -> None:
        """Test URI formatting with various characters."""
        uri = format_skill_uri("excel_advanced")

        assert uri == "skill://excel_advanced"

    def test_format_skill_uri_empty_string(self) -> None:
        """Test URI formatting with empty string."""
        uri = format_skill_uri("")

        assert uri == "skill://"


class TestSafeJsonDumps:
    """Tests for safe_json_dumps function."""

    def test_safe_json_dumps_simple_dict(self) -> None:
        """Test serializing simple dictionary."""
        data = {"name": "test", "value": 123}

        json_str = safe_json_dumps(data)

        assert "test" in json_str
        assert "123" in json_str
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["name"] == "test"

    def test_safe_json_dumps_with_path_objects(self, tmp_path: Path) -> None:
        """Test serializing data with Path objects."""
        data = {"path": tmp_path, "name": "test"}

        json_str = safe_json_dumps(data)

        # Path should be converted to string
        parsed = json.loads(json_str)
        assert isinstance(parsed["path"], str)
        assert tmp_path.name in parsed["path"]

    def test_safe_json_dumps_with_nested_paths(self, tmp_path: Path) -> None:
        """Test serializing nested data with Path objects."""
        data = {
            "skill": {
                "name": "test",
                "folder": tmp_path,
                "file": tmp_path / "SKILL.md",
            }
        }

        json_str = safe_json_dumps(data)

        parsed = json.loads(json_str)
        assert isinstance(parsed["skill"]["folder"], str)
        assert isinstance(parsed["skill"]["file"], str)

    def test_safe_json_dumps_custom_indent(self) -> None:
        """Test JSON dumps with custom indent."""
        data = {"key": "value"}

        json_str = safe_json_dumps(data, indent=4)

        # Should have indentation
        assert "    " in json_str

    def test_safe_json_dumps_with_list(self, tmp_path: Path) -> None:
        """Test serializing list with Path objects."""
        data = [tmp_path, "string", 123]

        json_str = safe_json_dumps(data)

        parsed = json.loads(json_str)
        assert isinstance(parsed[0], str)
        assert parsed[1] == "string"
        assert parsed[2] == 123


class TestValidateSkillName:
    """Tests for validate_skill_name function."""

    def test_validate_valid_skill_name(self) -> None:
        """Test validating a valid skill name."""
        is_valid, message = validate_skill_name("my-skill")

        assert is_valid is True
        assert message == ""

    def test_validate_skill_name_with_underscores(self) -> None:
        """Test validating skill name with underscores."""
        is_valid, message = validate_skill_name("my_skill")

        assert is_valid is True

    def test_validate_skill_name_with_numbers(self) -> None:
        """Test validating skill name with numbers."""
        is_valid, message = validate_skill_name("skill123")

        assert is_valid is True

    def test_validate_skill_name_alphanumeric_with_dash(self) -> None:
        """Test validating alphanumeric name with dashes."""
        is_valid, message = validate_skill_name("skill-name-v2")

        assert is_valid is True

    def test_validate_empty_skill_name(self) -> None:
        """Test validating empty skill name."""
        is_valid, message = validate_skill_name("")

        assert is_valid is False
        assert "empty" in message.lower()

    def test_validate_whitespace_only_skill_name(self) -> None:
        """Test validating whitespace-only skill name."""
        is_valid, message = validate_skill_name("   ")

        assert is_valid is False
        assert "empty" in message.lower()

    def test_validate_skill_name_with_special_characters(self) -> None:
        """Test validating skill name with special characters."""
        is_valid, message = validate_skill_name("my@skill")

        assert is_valid is False
        assert "alphanumeric" in message.lower() or "letters" in message.lower()

    def test_validate_skill_name_starting_with_number(self) -> None:
        """Test validating skill name starting with number."""
        is_valid, message = validate_skill_name("123skill")

        assert is_valid is False
        assert "number" in message.lower()

    def test_validate_skill_name_uppercase_warning(self) -> None:
        """Test validating uppercase skill name gives warning."""
        is_valid, message = validate_skill_name("MySkill")

        # Should still be valid but with warning
        assert is_valid is True
        assert "lowercase" in message.lower() or "warning" in message.lower()

    def test_validate_skill_name_with_spaces(self) -> None:
        """Test validating skill name with spaces."""
        is_valid, message = validate_skill_name("my skill")

        assert is_valid is False
        assert "alphanumeric" in message.lower() or "letters" in message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
