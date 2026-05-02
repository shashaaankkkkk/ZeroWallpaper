"""Favorites management for ZeroWallpaper."""

from __future__ import annotations

import json
from pathlib import Path

from zerowallpaper.core.config import _get_app_dir


class FavoritesManager:
    """Manage favorite wallpapers stored locally."""

    def __init__(self) -> None:
        self._path = _get_app_dir() / "favorites.json"
        self._favorites: set[str] = set()
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                self._favorites = set(data.get("favorites", []))
            except (json.JSONDecodeError, TypeError):
                self._favorites = set()

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({"favorites": sorted(self._favorites)}, indent=2)
        )

    def add(self, filename: str) -> None:
        self._favorites.add(filename)
        self._save()

    def remove(self, filename: str) -> None:
        self._favorites.discard(filename)
        self._save()

    def toggle(self, filename: str) -> bool:
        """Toggle favorite status. Returns True if now favorited."""
        if filename in self._favorites:
            self._favorites.discard(filename)
            self._save()
            return False
        else:
            self._favorites.add(filename)
            self._save()
            return True

    def is_favorite(self, filename: str) -> bool:
        return filename in self._favorites

    def get_all(self) -> list[str]:
        return sorted(self._favorites)

    @property
    def count(self) -> int:
        return len(self._favorites)
