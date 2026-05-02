"""Windows wallpaper setter using ctypes."""

from __future__ import annotations

import asyncio
from pathlib import Path

from zerowallpaper.platforms.base import WallpaperBackend


class WindowsBackend(WallpaperBackend):
    """Set wallpaper on Windows using SystemParametersInfoW."""

    async def set_wallpaper(self, image_path: Path) -> bool:
        abs_path = str(image_path.resolve())
        try:
            import ctypes
            SPI_SETDESKWALLPAPER = 0x0014
            SPIF_UPDATEINIFILE = 0x01
            SPIF_SENDCHANGE = 0x02
            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, abs_path,
                SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
            )
            return bool(result)
        except Exception:
            return False

    def get_name(self) -> str:
        return "Windows (SystemParametersInfoW)"
