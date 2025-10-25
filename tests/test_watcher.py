"""
Tests for the SkillWatcher (hot-reload functionality).

These tests use mocking to test file watching without
requiring actual file system operations.

Tests cover:
- Watcher initialization
- Starting and stopping the watcher
- File change event handling
- Debouncing logic
- Event filtering
- Lifecycle management
"""

import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_skills.watcher import SkillWatcher


@pytest.fixture
def mock_callback() -> AsyncMock:
    """Create a mock async callback function."""
    return AsyncMock()


@pytest.fixture
def watcher_path(tmp_path: Path) -> Path:
    """Create a temporary directory for watching."""
    watch_dir = tmp_path / "skills"
    watch_dir.mkdir()
    return watch_dir


@pytest.fixture
def mock_loop() -> Mock:
    """Create a mock event loop."""
    return Mock(spec=asyncio.AbstractEventLoop)


class TestWatcherInitialization:
    """Tests for watcher initialization."""

    def test_create_watcher(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test creating a watcher instance."""
        watcher = SkillWatcher(
            skills_dir=watcher_path,
            callback=mock_callback,
            loop=mock_loop,
            debounce_delay=0.5,
        )

        assert watcher.skills_dir == watcher_path.resolve()
        assert watcher.callback == mock_callback
        assert watcher.debounce_delay == 0.5
        assert watcher._watch_thread is None
        assert watcher._is_watching is False

    def test_watcher_default_debounce(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test watcher with default debounce delay."""
        watcher = SkillWatcher(
            skills_dir=watcher_path,
            callback=mock_callback,
            loop=mock_loop,
        )

        assert watcher.debounce_delay == 0.5  # Default


class TestWatcherLifecycle:
    """Tests for watcher lifecycle management."""

    @patch("mcp_skills.watcher.watch")
    def test_start_watcher(
        self,
        mock_watch: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test starting the watcher."""
        # Mock watch to return empty iterator
        mock_watch.return_value = iter([])

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()

        # Give thread a moment to start
        time.sleep(0.1)

        # Watcher should be marked as running
        assert watcher._is_watching is True
        assert watcher._watch_thread is not None

        # Cleanup
        watcher.stop()

    @patch("mcp_skills.watcher.watch")
    def test_stop_watcher(
        self,
        mock_watch: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test stopping the watcher."""
        # Mock watch to return empty iterator
        mock_watch.return_value = iter([])

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()
        time.sleep(0.1)  # Let thread start

        watcher.stop()

        # Watcher should be marked as not running
        assert watcher._is_watching is False
        assert watcher._stop_event.is_set()

    def test_stop_watcher_without_start(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test stopping watcher that was never started."""
        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        # Should not raise error
        watcher.stop()

        # Watcher should remain not watching
        assert watcher._is_watching is False

    @patch("mcp_skills.watcher.watch")
    def test_start_already_running(
        self,
        mock_watch: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test starting watcher that's already running."""
        mock_watch.return_value = iter([])

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()
        time.sleep(0.1)

        # Try to start again
        watcher.start()

        # Should still be watching
        assert watcher._is_watching is True

        watcher.stop()


class TestWatcherRepr:
    """Tests for string representation."""

    def test_watcher_repr(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test __repr__ method."""
        watcher = SkillWatcher(
            skills_dir=watcher_path,
            callback=mock_callback,
            loop=mock_loop,
            debounce_delay=0.5,
        )

        repr_str = repr(watcher)

        assert "SkillWatcher" in repr_str
        assert str(watcher_path.resolve()) in repr_str
        assert "stopped" in repr_str

    @patch("mcp_skills.watcher.watch")
    def test_watcher_repr_when_running(
        self,
        mock_watch: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test __repr__ when watcher is running."""
        mock_watch.return_value = iter([])

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()
        time.sleep(0.1)

        repr_str = repr(watcher)

        assert "watching" in repr_str

        watcher.stop()


class TestWatcherIsWatching:
    """Tests for is_watching method."""

    def test_is_watching_false_initially(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test is_watching returns False initially."""
        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        assert watcher.is_watching() is False

    @patch("mcp_skills.watcher.watch")
    def test_is_watching_true_after_start(
        self,
        mock_watch: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test is_watching returns True after start."""
        mock_watch.return_value = iter([])

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()
        time.sleep(0.1)

        assert watcher.is_watching() is True

        watcher.stop()

    @patch("mcp_skills.watcher.watch")
    def test_is_watching_false_after_stop(
        self,
        mock_watch: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test is_watching returns False after stop."""
        mock_watch.return_value = iter([])

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()
        time.sleep(0.1)

        watcher.stop()

        assert watcher.is_watching() is False


class TestWatcherContextManager:
    """Tests for context manager protocol."""

    @patch("mcp_skills.watcher.watch")
    def test_context_manager_starts_and_stops(
        self,
        mock_watch: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test that context manager starts and stops watcher."""
        mock_watch.return_value = iter([])

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        with watcher:
            time.sleep(0.1)  # Let thread start
            # Should be watching inside context
            assert watcher.is_watching() is True

        # Should be stopped after context
        assert watcher.is_watching() is False


class TestWatcherFileValidation:
    """Tests for file validation logic."""

    def test_is_skill_file_valid(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test validation of valid SKILL.md file."""
        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        # Create valid skill folder structure
        skill_folder = watcher_path / "my-skill"
        skill_folder.mkdir()
        skill_file = skill_folder / "SKILL.md"

        assert watcher._is_skill_file_in_valid_folder(skill_file) is True

    def test_is_skill_file_wrong_name(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test validation rejects non-SKILL.md files."""
        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        skill_folder = watcher_path / "my-skill"
        skill_folder.mkdir()
        wrong_file = skill_folder / "README.md"

        assert watcher._is_skill_file_in_valid_folder(wrong_file) is False

    def test_is_skill_file_hidden_folder(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test validation rejects hidden folders."""
        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        hidden_folder = watcher_path / ".hidden"
        hidden_folder.mkdir()
        skill_file = hidden_folder / "SKILL.md"

        assert watcher._is_skill_file_in_valid_folder(skill_file) is False

    def test_is_skill_file_private_folder(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test validation rejects private folders."""
        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        private_folder = watcher_path / "_private"
        private_folder.mkdir()
        skill_file = private_folder / "SKILL.md"

        assert watcher._is_skill_file_in_valid_folder(skill_file) is False

    def test_is_skill_file_nested_folder(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test validation rejects nested folders."""
        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        parent_folder = watcher_path / "parent"
        parent_folder.mkdir()
        nested_folder = parent_folder / "nested"
        nested_folder.mkdir()
        skill_file = nested_folder / "SKILL.md"

        assert watcher._is_skill_file_in_valid_folder(skill_file) is False

    def test_is_skill_file_in_root(
        self, watcher_path: Path, mock_callback: AsyncMock, mock_loop: Mock
    ) -> None:
        """Test validation rejects SKILL.md in root."""
        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        skill_file = watcher_path / "SKILL.md"

        assert watcher._is_skill_file_in_valid_folder(skill_file) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
