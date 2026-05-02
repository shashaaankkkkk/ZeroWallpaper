"""Recent wallpaper history tracking."""

from __future__ import annotations

import json
import time
from pathlib import Path

from zerowallpaper.core.config import _get_app_dir

MAX_HISTORY = 50


class HistoryManager:
    """Track recently applied wallpapers."""

    def __init__(self) -> None:
        self._path = _get_app_dir() / "recent.json"
        self._history: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                self._history = data.get("recent", [])
            except (json.JSONDecodeError, TypeError):
                self._history = []

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({"recent": self._history}, indent=2)
        )

    def add(self, filename: str) -> None:
        """Add a wallpaper to history."""
        # Remove duplicate if exists
        self._history = [h for h in self._history if h["filename"] != filename]
        # Add to front
        self._history.insert(0, {
            "filename": filename,
            "applied_at": time.time(),
        })
        # Trim to max
        self._history = self._history[:MAX_HISTORY]
        self._save()

    def get_recent(self, limit: int = 10) -> list[str]:
        """Get recent wallpaper filenames."""
        return [h["filename"] for h in self._history[:limit]]

    @property
    def count(self) -> int:
        return len(self._history)
