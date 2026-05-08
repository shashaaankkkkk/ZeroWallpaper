"""Playlist management for ZeroWallpaper."""

from __future__ import annotations

import json
from pathlib import Path

from zerowallpaper.core.config import _get_app_dir


class PlaylistManager:
    """Manage multiple playlists of wallpapers."""

    def __init__(self) -> None:
        self._path = _get_app_dir() / "playlist.json"
        self._playlists: dict[str, list[str]] = {"Default": []}
        self._active: str = "Default"
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                
                # Migration from old flat list format
                if "playlist" in data:
                    self._playlists = {"Default": data["playlist"]}
                    self._active = "Default"
                    self._save() # Save in new format immediately
                    return

                self._playlists = data.get("playlists", {"Default": []})
                self._active = data.get("active", "Default")
                
                # Ensure active exists
                if self._active not in self._playlists:
                    self._active = next(iter(self._playlists.keys()), "Default")
                    if self._active not in self._playlists:
                        self._playlists[self._active] = []

            except (json.JSONDecodeError, TypeError):
                self._playlists = {"Default": []}
                self._active = "Default"

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({
                "active": self._active,
                "playlists": self._playlists
            }, indent=2)
        )

    @property
    def active_name(self) -> str:
        return self._active

    @property
    def playlist_names(self) -> list[str]:
        return sorted(self._playlists.keys())

    def set_active(self, name: str) -> bool:
        if name in self._playlists:
            self._active = name
            self._save()
            return True
        return False

    def create_playlist(self, name: str) -> bool:
        name = name.strip()
        if not name or name in self._playlists:
            return False
        self._playlists[name] = []
        self._save()
        return True

    def delete_playlist(self, name: str) -> bool:
        if name == "Default" or name not in self._playlists:
            return False
        
        del self._playlists[name]
        if self._active == name:
            self._active = "Default"
        self._save()
        return True

    def rename_playlist(self, old_name: str, new_name: str) -> bool:
        new_name = new_name.strip()
        if old_name not in self._playlists or new_name in self._playlists or not new_name:
            return False
        
        self._playlists[new_name] = self._playlists.pop(old_name)
        if self._active == old_name:
            self._active = new_name
        self._save()
        return True

    def add(self, filename: str, playlist_name: str | None = None) -> None:
        target = playlist_name or self._active
        if target in self._playlists:
            if filename not in self._playlists[target]:
                self._playlists[target].append(filename)
                self._save()

    def remove(self, filename: str, playlist_name: str | None = None) -> None:
        target = playlist_name or self._active
        if target in self._playlists:
            if filename in self._playlists[target]:
                self._playlists[target].remove(filename)
                self._save()

    def toggle(self, filename: str, playlist_name: str | None = None) -> bool:
        target = playlist_name or self._active
        if target not in self._playlists:
            return False
            
        if filename in self._playlists[target]:
            self._playlists[target].remove(filename)
            self._save()
            return False
        else:
            self._playlists[target].append(filename)
            self._save()
            return True

    def is_in_playlist(self, filename: str, playlist_name: str | None = None) -> bool:
        target = playlist_name or self._active
        return filename in self._playlists.get(target, [])

    def get_all(self, playlist_name: str | None = None) -> list[str]:
        target = playlist_name or self._active
        return list(self._playlists.get(target, []))

    def get_next(self) -> str | None:
        """Get next WP from active playlist and cycle."""
        playlist = self._playlists.get(self._active, [])
        if not playlist:
            return None
        
        filename = playlist.pop(0)
        playlist.append(filename)
        self._save()
        return filename

    def peek_upcoming(self, count: int = 3) -> list[str]:
        return self._playlists.get(self._active, [])[:count]

    @property
    def count(self) -> int:
        return len(self._playlists.get(self._active, []))
