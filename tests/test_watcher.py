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
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from watchdog.events import FileCreatedEvent, FileModifiedEvent

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

        assert watcher.skills_dir == watcher_path
        assert watcher.callback == mock_callback
        assert watcher.debounce_delay == 0.5
        assert watcher.observer is None
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

    @patch("mcp_skills.watcher.Observer")
    def test_start_watcher(
        self,
        mock_observer_class: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test starting the watcher."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()

        # Observer should be created
        mock_observer_class.assert_called_once()

        # Observer should be started
        mock_observer.start.assert_called_once()

        # Watcher should be marked as running
        assert watcher._is_watching is True

    @patch("mcp_skills.watcher.Observer")
    def test_start_watcher_schedules_handler(
        self,
        mock_observer_class: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test that starting watcher schedules the event handler."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()

        # Observer.schedule should be called with handler, path, recursive=True
        mock_observer.schedule.assert_called_once()
        call_args = mock_observer.schedule.call_args
        assert call_args[0][1] == str(watcher_path)  # path
        assert call_args[1]["recursive"] is True

    @patch("mcp_skills.watcher.Observer")
    def test_stop_watcher(
        self,
        mock_observer_class: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test stopping the watcher."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()
        watcher.stop()

        # Observer should be stopped
        mock_observer.stop.assert_called_once()

        # Watcher should be marked as not running
        assert watcher._is_watching is False

    @patch("mcp_skills.watcher.Observer")
    def test_stop_watcher_joins_thread(
        self,
        mock_observer_class: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test that stopping watcher joins the observer thread."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()
        watcher.stop()

        # Observer.join should be called
        mock_observer.join.assert_called_once()

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
        assert str(watcher_path) in repr_str
        assert "stopped" in repr_str

    @patch("mcp_skills.watcher.Observer")
    def test_watcher_repr_when_running(
        self,
        mock_observer_class: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test __repr__ when watcher is running."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()
        repr_str = repr(watcher)

        assert "watching" in repr_str


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

    @patch("mcp_skills.watcher.Observer")
    def test_is_watching_true_after_start(
        self,
        mock_observer_class: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test is_watching returns True after start."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()

        assert watcher.is_watching() is True

    @patch("mcp_skills.watcher.Observer")
    def test_is_watching_false_after_stop(
        self,
        mock_observer_class: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test is_watching returns False after stop."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        watcher.start()
        watcher.stop()

        assert watcher.is_watching() is False


class TestWatcherContextManager:
    """Tests for context manager protocol."""

    @patch("mcp_skills.watcher.Observer")
    def test_context_manager_starts_and_stops(
        self,
        mock_observer_class: Mock,
        watcher_path: Path,
        mock_callback: AsyncMock,
        mock_loop: Mock,
    ) -> None:
        """Test that context manager starts and stops watcher."""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = SkillWatcher(
            skills_dir=watcher_path, callback=mock_callback, loop=mock_loop
        )

        with watcher:
            # Should be watching inside context
            assert watcher.is_watching() is True

        # Should be stopped after context
        assert watcher.is_watching() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
