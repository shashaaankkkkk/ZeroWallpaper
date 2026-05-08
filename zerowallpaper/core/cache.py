"""Cache management for downloaded wallpapers and API responses."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from zerowallpaper.core.config import AppConfig


class CacheManager:
    """Manages local caching of wallpapers, thumbnails, and index data."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure all cache directories exist."""
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        self.config.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.config.wallpapers_dir.mkdir(parents=True, exist_ok=True)

    # --- Index cache ---

    @property
    def index_path(self) -> Path:
        """Path to cached index file."""
        return self.config.cache_dir / "index.json"

    def get_index(self) -> dict[str, Any] | None:
        """Load cached index if it exists and is not expired."""
        if not self.index_path.exists():
            return None

        try:
            data = json.loads(self.index_path.read_text())
            updated_at = data.get("updated_at", 0)
            ttl_seconds = self.config.cache_ttl_hours * 3600

            if time.time() - updated_at > ttl_seconds:
                return None  # Expired

            return data
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def save_index(self, data: dict[str, Any]) -> None:
        """Save index data to cache."""
        data["updated_at"] = time.time()
        self.index_path.write_text(json.dumps(data, indent=2))

    def force_invalidate_index(self) -> None:
        """Force invalidate the index cache."""
        if self.index_path.exists():
            self.index_path.unlink()

    # --- Image cache ---

    def get_wallpaper_path(self, filename: str) -> Path:
        """Get the path where a wallpaper would be cached."""
        return self.config.wallpapers_dir / filename

    def get_thumbnail_path(self, filename: str) -> Path:
        """Get the path where a thumbnail would be cached."""
        # Use .png for all thumbnails
        stem = Path(filename).stem
        return self.config.thumbnails_dir / f"{stem}.png"

    def is_wallpaper_cached(self, filename: str) -> bool:
        """Check if a wallpaper is cached locally."""
        return self.get_wallpaper_path(filename).exists()

    def is_thumbnail_cached(self, filename: str) -> bool:
        """Check if a thumbnail is cached locally."""
        return self.get_thumbnail_path(filename).exists()

    def save_wallpaper(self, filename: str, data: bytes) -> Path:
        """Save wallpaper image data to cache."""
        path = self.get_wallpaper_path(filename)
        path.write_bytes(data)
        return path

    def save_thumbnail(self, filename: str, data: bytes) -> Path:
        """Save thumbnail data to cache."""
        path = self.get_thumbnail_path(filename)
        path.write_bytes(data)
        return path

    # --- Stats ---

    def get_cached_wallpaper_count(self) -> int:
        """Get count of cached wallpapers."""
        return len(list(self.config.wallpapers_dir.glob("*")))

    def get_cached_thumbnail_count(self) -> int:
        """Get count of cached thumbnails."""
        return len(list(self.config.thumbnails_dir.glob("*")))

    def get_cache_size_mb(self) -> float:
        """Get total cache size in MB."""
        total = 0
        for f in self.config.cache_dir.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total / (1024 * 1024)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "wallpapers": self.get_cached_wallpaper_count(),
            "thumbnails": self.get_cached_thumbnail_count(),
            "size_mb": round(self.get_cache_size_mb(), 1),
            "has_index": self.index_path.exists(),
        }

    def cleanup(self, max_age_days: int = 7) -> int:
        """Clean up files older than max_age_days.
        
        Returns the number of files deleted.
        """
        deleted_count = 0
        now = time.time()
        max_age_seconds = max_age_days * 86400

        # Directories to clean
        dirs_to_clean = [self.config.wallpapers_dir, self.config.thumbnails_dir]

        for directory in dirs_to_clean:
            if not directory.exists():
                continue
            
            for f in directory.glob("*"):
                if f.is_file():
                    # If file is older than max_age, delete it
                    if now - f.stat().st_mtime > max_age_seconds:
                        try:
                            f.unlink()
                            deleted_count += 1
                        except Exception:
                            pass
        
        return deleted_count
