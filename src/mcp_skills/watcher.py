"""
File system watcher for hot-reloading skills.

This module monitors the skills directory for changes to SKILL.md files
and triggers reload callbacks. It includes debouncing to prevent reload
spam during rapid file edits.

**Watching Rules:**
1. Only watch SKILL.md files in valid skill folders
2. Debounce rapid changes (default 500ms)
3. Thread-safe callback execution
4. Proper cleanup on shutdown
"""

import asyncio
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from mcp_skills.scanner import SkillScanner

logger = logging.getLogger(__name__)


class SkillFileHandler(FileSystemEventHandler):
    """
    File system event handler for SKILL.md files.

    This handler filters events to only process SKILL.md files in valid
    skill folders, following the strict folder structure requirements.

    **Valid Events:**
        ✓ /skills/my-skill/SKILL.md modified
        ✓ /skills/new-skill/SKILL.md created
        ✓ /skills/old-skill/SKILL.md deleted

    **Ignored Events:**
        ✗ /skills/SKILL.md (not in folder)
        ✗ /skills/.hidden/SKILL.md (hidden folder)
        ✗ /skills/my-skill/README.md (not SKILL.md)
        ✗ /skills/__pycache__/SKILL.md (system folder)

    Args:
        callback: Async function to call when a valid SKILL.md changes
        loop: Asyncio event loop for callback execution
        skills_dir: Root skills directory path
        debounce_delay: Delay in seconds before triggering callback
    """

    def __init__(
        self,
        callback: Callable[[Path], None],
        loop: asyncio.AbstractEventLoop,
        skills_dir: Path,
        debounce_delay: float = 0.5,
    ) -> None:
        """Initialize the file handler."""
        super().__init__()
        self.callback = callback
        self.loop = loop
        self.skills_dir = Path(skills_dir)
        self.debounce_delay = debounce_delay
        self._debounce_timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        logger.debug(
            f"Initialized SkillFileHandler with {debounce_delay}s debounce delay"
        )

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory:
            self._handle_event(event.src_path, "modified")

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory:
            self._handle_event(event.src_path, "created")

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if not event.is_directory:
            self._handle_event(event.src_path, "deleted")

    def _handle_event(self, path_str: str, event_type: str) -> None:
        """
        Handle a file system event with debouncing.

        Args:
            path_str: File system path that changed
            event_type: Type of event (modified, created, deleted)
        """
        path = Path(path_str)

        # Only process valid SKILL.md files in proper folder structure
        if not self._is_skill_file_in_valid_folder(path):
            return

        folder_name = path.parent.name
        logger.debug(
            f"Detected {event_type} event for skill '{folder_name}': {path}"
        )

        # Debounce: cancel existing timer and start new one
        with self._lock:
            # Cancel existing timer for this path
            if path_str in self._debounce_timers:
                self._debounce_timers[path_str].cancel()

            # Create new timer
            timer = threading.Timer(
                self.debounce_delay,
                self._trigger_callback,
                args=(path, event_type),
            )
            self._debounce_timers[path_str] = timer
            timer.start()

    def _trigger_callback(self, path: Path, event_type: str) -> None:
        """
        Trigger the reload callback after debounce delay.

        Args:
            path: Path to the changed SKILL.md file
            event_type: Type of event
        """
        folder_name = path.parent.name

        with self._lock:
            # Remove timer from dict
            path_str = str(path)
            if path_str in self._debounce_timers:
                del self._debounce_timers[path_str]

        logger.info(
            f"Triggering reload for skill folder '{folder_name}' "
            f"(event: {event_type})"
        )

        # Execute callback in the event loop
        asyncio.run_coroutine_threadsafe(self.callback(path), self.loop)

    def _is_skill_file_in_valid_folder(self, path: Path) -> bool:
        """
        Check if the file is a SKILL.md in a valid folder structure.

        **Validation Rules:**
        1. Must be named SKILL.md
        2. Must be in a folder that's a direct child of skills_dir
        3. Must not be in ignored/hidden folders

        Args:
            path: File system path that changed

        Returns:
            True if this is a SKILL.md in a proper skill folder

        Example:
            ✓ /skills/my-skill/SKILL.md
            ✗ /skills/SKILL.md
            ✗ /skills/.hidden/SKILL.md
            ✗ /skills/subfolder/nested/SKILL.md
        """
        # Must be named SKILL.md
        if path.name != "SKILL.md":
            return False

        # Must be in a folder
        parent = path.parent

        # Folder must be a direct child of skills_dir
        if parent.parent != self.skills_dir:
            return False

        # Must not be in ignored folders
        if parent.name in SkillScanner.IGNORED_FOLDERS:
            logger.debug(f"Ignoring change in system folder: {parent.name}")
            return False

        # Must not be hidden
        if parent.name.startswith("."):
            logger.debug(f"Ignoring change in hidden folder: {parent.name}")
            return False

        # Must not be private
        if parent.name.startswith("_"):
            logger.debug(f"Ignoring change in private folder: {parent.name}")
            return False

        return True

    def cleanup(self) -> None:
        """Cancel all pending debounce timers."""
        with self._lock:
            for timer in self._debounce_timers.values():
                timer.cancel()
            self._debounce_timers.clear()
        logger.debug("Cleaned up all debounce timers")


class SkillWatcher:
    """
    File system watcher for skill hot-reloading.

    Monitors the skills directory for changes to SKILL.md files and
    triggers a reload callback when valid changes are detected.

    **Features:**
    - Watches only SKILL.md files in valid skill folders
    - Debounces rapid changes to prevent reload spam
    - Thread-safe operation
    - Graceful shutdown with cleanup

    Example:
        >>> async def on_change(path: Path):
        ...     print(f"Skill changed: {path}")
        ...
        >>> watcher = SkillWatcher(
        ...     skills_dir=Path("/skills"),
        ...     callback=on_change,
        ...     loop=asyncio.get_event_loop()
        ... )
        >>> watcher.start()
        >>> # ... later ...
        >>> watcher.stop()
    """

    def __init__(
        self,
        skills_dir: Path,
        callback: Callable[[Path], None],
        loop: asyncio.AbstractEventLoop,
        debounce_delay: float = 0.5,
    ) -> None:
        """
        Initialize the skill watcher.

        Args:
            skills_dir: Root directory containing skill folders
            callback: Async function to call when a SKILL.md file changes
            loop: Asyncio event loop for callback execution
            debounce_delay: Delay in seconds before triggering callback

        Example:
            >>> async def reload_skill(path: Path):
            ...     print(f"Reloading: {path}")
            ...
            >>> watcher = SkillWatcher(
            ...     Path("/skills"),
            ...     reload_skill,
            ...     asyncio.get_event_loop(),
            ...     debounce_delay=0.5
            ... )
        """
        self.skills_dir = Path(skills_dir)
        self.callback = callback
        self.loop = loop
        self.debounce_delay = debounce_delay

        self.event_handler = SkillFileHandler(
            callback=callback,
            loop=loop,
            skills_dir=skills_dir,
            debounce_delay=debounce_delay,
        )

        self.observer: Optional[Observer] = None
        self._is_watching = False

        logger.debug(f"Initialized SkillWatcher for directory: {self.skills_dir}")

    def start(self) -> None:
        """
        Start watching the skills directory.

        Creates an observer thread that monitors file system events.
        The observer runs in the background until stop() is called.

        Example:
            >>> watcher.start()
            >>> print("Watching for changes...")

        Note:
            This method is idempotent - calling it multiple times has no effect
            if the watcher is already running.
        """
        if self._is_watching:
            logger.warning("Watcher is already running")
            return

        if not self.skills_dir.exists():
            logger.error(
                f"Cannot start watcher: skills directory does not exist: {self.skills_dir}"
            )
            return

        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.skills_dir),
            recursive=True,  # Watch subdirectories
        )
        self.observer.start()
        self._is_watching = True

        logger.info(
            f"Started watching {self.skills_dir} for SKILL.md changes "
            f"(debounce: {self.debounce_delay}s)"
        )
        logger.info(
            "Hot-reload enabled: SKILL.md files in skill folders will be "
            "automatically reloaded when modified"
        )

    def stop(self) -> None:
        """
        Stop watching the skills directory.

        Stops the observer thread and cleans up any pending debounce timers.

        Example:
            >>> watcher.stop()
            >>> print("Stopped watching")

        Note:
            This method is idempotent - calling it multiple times has no effect
            if the watcher is already stopped.
        """
        if not self._is_watching:
            logger.debug("Watcher is not running")
            return

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.observer = None

        self.event_handler.cleanup()
        self._is_watching = False

        logger.info("Stopped watching skills directory")

    def is_watching(self) -> bool:
        """
        Check if the watcher is currently active.

        Returns:
            True if watcher is running, False otherwise

        Example:
            >>> if watcher.is_watching():
            ...     print("Watcher is active")
        """
        return self._is_watching

    def __enter__(self) -> "SkillWatcher":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: any, exc_val: any, exc_tb: any) -> None:
        """Context manager exit."""
        self.stop()

    def __repr__(self) -> str:
        """String representation."""
        status = "watching" if self._is_watching else "stopped"
        return f"SkillWatcher(skills_dir={self.skills_dir}, status={status})"
