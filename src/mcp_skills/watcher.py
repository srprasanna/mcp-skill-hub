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

from watchfiles import Change, watch

from mcp_skills.scanner import SkillScanner

logger = logging.getLogger(__name__)


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
        self.skills_dir = Path(skills_dir).resolve()
        self.callback = callback
        self.loop = loop
        self.debounce_delay = debounce_delay

        self._watch_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_watching = False
        self._debounce_timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

        logger.debug(f"Initialized SkillWatcher for directory: {self.skills_dir}")

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

    def _handle_changes(self, changes: set[tuple[Change, str]]) -> None:
        """
        Handle file system changes with debouncing.

        Args:
            changes: Set of (change_type, path) tuples from watchfiles
        """
        for change_type, path_str in changes:
            path = Path(path_str)

            # Only process valid SKILL.md files in proper folder structure
            if not self._is_skill_file_in_valid_folder(path):
                continue

            folder_name = path.parent.name
            event_type = change_type.name.lower()
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

    def _watch_loop(self) -> None:
        """
        Watch loop that runs in a separate thread.

        This loop uses watchfiles to monitor the skills directory and
        processes changes as they occur.
        """
        logger.info(
            f"Started watching {self.skills_dir} for SKILL.md changes "
            f"(debounce: {self.debounce_delay}s)"
        )
        logger.info(
            "Hot-reload enabled: SKILL.md files in skill folders will be "
            "automatically reloaded when modified"
        )

        try:
            # watchfiles.watch is an iterator that yields sets of changes
            for changes in watch(
                self.skills_dir,
                stop_event=self._stop_event,
                recursive=True,
                # Only watch for .md files to reduce overhead
                watch_filter=lambda change, path: path.endswith(".md"),
            ):
                if self._stop_event.is_set():
                    break

                self._handle_changes(changes)

        except Exception as e:
            logger.error(f"Error in watch loop: {e}", exc_info=True)
        finally:
            logger.info("Watch loop ended")

    def start(self) -> None:
        """
        Start watching the skills directory.

        Creates a background thread that monitors file system events.
        The thread runs until stop() is called.

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

        self._stop_event.clear()
        self._watch_thread = threading.Thread(
            target=self._watch_loop, name="SkillWatcher", daemon=True
        )
        self._watch_thread.start()
        self._is_watching = True

    def stop(self) -> None:
        """
        Stop watching the skills directory.

        Stops the watch thread and cleans up any pending debounce timers.

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

        # Signal the watch loop to stop
        self._stop_event.set()

        # Wait for the thread to finish
        if self._watch_thread and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=5.0)
            self._watch_thread = None

        # Cancel all pending timers
        with self._lock:
            for timer in self._debounce_timers.values():
                timer.cancel()
            self._debounce_timers.clear()

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
