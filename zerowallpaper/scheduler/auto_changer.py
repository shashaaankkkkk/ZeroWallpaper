"""Auto wallpaper rotation scheduler."""

from __future__ import annotations

import asyncio
import random
from typing import Any, Callable, Awaitable

from zerowallpaper.core.config import AppConfig


class AutoChanger:
    """Background task that periodically changes wallpapers."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._task: asyncio.Task | None = None
        self._running = False
        self._interval_minutes = config.auto_change.interval_minutes
        self._on_change: Callable[..., Awaitable] | None = None
        self._filter_tags: list[str] = list(config.auto_change.tags)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def interval_minutes(self) -> int:
        return self._interval_minutes

    def set_callback(self, callback: Callable[..., Awaitable]) -> None:
        """Set the callback for when wallpaper should change.

        Callback receives no args; the caller handles picking and setting.
        """
        self._on_change = callback

    def set_interval(self, minutes: int) -> None:
        self._interval_minutes = max(1, minutes)

    def set_filter_tags(self, tags: list[str]) -> None:
        self._filter_tags = list(tags)

    def start(self) -> None:
        """Start auto-change background task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    def stop(self) -> None:
        """Stop auto-change background task."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    def toggle(self) -> bool:
        """Toggle auto-change. Returns True if now running."""
        if self._running:
            self.stop()
            return False
        else:
            self.start()
            return True

    async def _run_loop(self) -> None:
        """Main auto-change loop."""
        try:
            while self._running:
                await asyncio.sleep(self._interval_minutes * 60)
                if self._running and self._on_change:
                    try:
                        await self._on_change()
                    except Exception:
                        pass  # Don't crash on callback errors
        except asyncio.CancelledError:
            pass
