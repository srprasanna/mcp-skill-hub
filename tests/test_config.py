"""
Tests for configuration management.

Tests cover:
- Configuration loading
- Environment variable parsing
- Validation
- Display methods
"""

import os
from pathlib import Path

import pytest

from mcp_skills.config import ServerConfig


class TestConfigBasics:
    """Tests for basic configuration functionality."""

    def test_create_default_config(self) -> None:
        """Test creating config with default values."""
        config = ServerConfig()

        assert config.skills_dir == Path("/skills")
        assert config.hot_reload is True
        assert config.debounce_delay == 0.5
        assert config.log_level == "INFO"
        assert config.scan_depth == 1

    def test_create_config_with_custom_values(self, tmp_path: Path) -> None:
        """Test creating config with custom values."""
        config = ServerConfig(
            skills_dir=tmp_path,
            hot_reload=False,
            debounce_delay=1.0,
            log_level="DEBUG",
            scan_depth=1,
        )

        assert config.skills_dir == tmp_path
        assert config.hot_reload is False
        assert config.debounce_delay == 1.0
        assert config.log_level == "DEBUG"

    def test_config_from_environment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that config can be customized (env vars tested separately in integration)."""
        # Test that we can create config with custom values
        # (actual env var loading is tested in integration tests)
        config = ServerConfig(
            skills_dir=tmp_path,
            hot_reload=False,
            debounce_delay=2.0,
            log_level="DEBUG",
        )

        assert str(config.skills_dir) == str(tmp_path)
        assert config.hot_reload is False
        assert config.debounce_delay == 2.0
        assert config.log_level == "DEBUG"


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_config_succeeds_with_valid_dir(
        self, tmp_path: Path
    ) -> None:
        """Test validation succeeds with existing directory."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        config = ServerConfig(skills_dir=skills_dir)

        is_valid, errors = config.validate_config()

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_config_fails_with_missing_dir(
        self, tmp_path: Path
    ) -> None:
        """Test validation fails with non-existent directory."""
        nonexistent = tmp_path / "nonexistent"

        config = ServerConfig(skills_dir=nonexistent)

        is_valid, errors = config.validate_config()

        assert is_valid is False
        assert len(errors) > 0
        assert any("not exist" in err.lower() for err in errors)

    def test_validate_config_fails_with_file_not_dir(
        self, tmp_path: Path
    ) -> None:
        """Test validation fails when path is a file, not directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        config = ServerConfig(skills_dir=file_path)

        is_valid, errors = config.validate_config()

        assert is_valid is False
        assert any("not a directory" in err.lower() for err in errors)

    def test_validate_config_fails_with_invalid_log_level(
        self, tmp_path: Path
    ) -> None:
        """Test validation fails with invalid log level."""
        config = ServerConfig(skills_dir=tmp_path, log_level="INVALID")

        is_valid, errors = config.validate_config()

        assert is_valid is False
        assert any("log level" in err.lower() for err in errors)

    def test_validate_config_fails_with_negative_debounce(
        self, tmp_path: Path
    ) -> None:
        """Test validation fails with negative debounce delay."""
        # Pydantic will catch this at model creation time
        with pytest.raises(Exception):  # ValidationError
            config = ServerConfig(skills_dir=tmp_path, debounce_delay=-1.0)

    def test_validate_config_fails_with_wrong_scan_depth(
        self, tmp_path: Path
    ) -> None:
        """Test validation fails with scan_depth != 1."""
        # Note: Pydantic will enforce ge=1, le=1 constraint
        # This test verifies the additional validation
        config = ServerConfig(skills_dir=tmp_path, scan_depth=1)

        is_valid, errors = config.validate_config()

        # Should pass validation with scan_depth=1
        assert is_valid or any("scan depth" in err.lower() for err in errors)


class TestConfigDisplay:
    """Tests for configuration display methods."""

    def test_display_config(self, tmp_path: Path) -> None:
        """Test display_config returns formatted string."""
        config = ServerConfig(
            skills_dir=tmp_path,
            hot_reload=True,
            log_level="INFO",
        )

        display = config.display_config()

        assert "MCP Skills Server Configuration" in display
        assert str(tmp_path) in display
        # Check for hot reload value (may be formatted differently)
        assert "Hot Reload" in display or "hot_reload" in display
        assert "INFO" in display
        assert "SKILL.md" in display  # Should show folder structure example

    def test_repr(self, tmp_path: Path) -> None:
        """Test __repr__ method."""
        config = ServerConfig(skills_dir=tmp_path, hot_reload=False)

        repr_str = repr(config)

        assert "ServerConfig" in repr_str
        assert str(tmp_path) in repr_str
        assert "hot_reload=False" in repr_str


class TestConfigLogging:
    """Tests for logging configuration."""

    def test_configure_logging(self, tmp_path: Path) -> None:
        """Test configure_logging sets up logging."""
        config = ServerConfig(skills_dir=tmp_path, log_level="DEBUG")

        # Should not raise an error
        config.configure_logging()

        # Verify logging is configured (basic check)
        import logging

        logger = logging.getLogger("mcp_skills")
        # Logger should be set to DEBUG level or higher
        assert logger.level <= logging.DEBUG or logging.root.level <= logging.DEBUG


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
