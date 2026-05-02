"""Abstract base for wallpaper setter backends."""

from __future__ import annotations

import platform
import sys
from abc import ABC, abstractmethod
from pathlib import Path


class WallpaperBackend(ABC):
    """Abstract wallpaper setter backend."""

    @abstractmethod
    async def set_wallpaper(self, image_path: Path) -> bool:
        """Set the desktop wallpaper.

        Args:
            image_path: Absolute path to the image file.

        Returns:
            True if successful.
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get the backend name."""
        ...


def get_backend() -> WallpaperBackend:
    """Auto-detect OS and return the appropriate backend."""
    system = platform.system().lower()

    if system == "darwin":
        from zerowallpaper.platforms.macos import MacOSBackend
        return MacOSBackend()
    elif system == "linux":
        from zerowallpaper.platforms.linux import LinuxBackend
        return LinuxBackend()
    elif system == "windows":
        from zerowallpaper.platforms.windows import WindowsBackend
        return WindowsBackend()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
