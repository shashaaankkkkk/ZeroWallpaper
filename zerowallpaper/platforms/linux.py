"""Linux wallpaper setter supporting GNOME and KDE."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from zerowallpaper.platforms.base import WallpaperBackend


class LinuxBackend(WallpaperBackend):
    """Set wallpaper on Linux (GNOME via gsettings, KDE via qdbus)."""

    def __init__(self) -> None:
        self._de = self._detect_de()

    def _detect_de(self) -> str:
        de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in de or "unity" in de or "budgie" in de:
            return "gnome"
        elif "kde" in de or "plasma" in de:
            return "kde"
        elif "xfce" in de:
            return "xfce"
        elif "mate" in de:
            return "mate"
        elif "cinnamon" in de:
            return "cinnamon"
        return "gnome"  # Default fallback

    async def set_wallpaper(self, image_path: Path) -> bool:
        abs_path = str(image_path.resolve())
        uri = f"file://{abs_path}"

        try:
            if self._de == "gnome":
                return await self._set_gnome(uri)
            elif self._de == "kde":
                return await self._set_kde(abs_path)
            elif self._de == "xfce":
                return await self._set_xfce(abs_path)
            elif self._de == "cinnamon":
                return await self._set_cinnamon(uri)
            elif self._de == "mate":
                return await self._set_mate(uri)
            else:
                return await self._set_gnome(uri)
        except Exception:
            return False

    async def _run(self, *args: str) -> bool:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0

    async def _set_gnome(self, uri: str) -> bool:
        r1 = await self._run(
            "gsettings", "set", "org.gnome.desktop.background",
            "picture-uri", uri,
        )
        r2 = await self._run(
            "gsettings", "set", "org.gnome.desktop.background",
            "picture-uri-dark", uri,
        )
        return r1 or r2

    async def _set_kde(self, path: str) -> bool:
        script = f"""
var allDesktops = desktops();
for (i=0; i<allDesktops.length; i++) {{
    d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
    d.writeConfig("Image", "file://{path}");
}}
"""
        return await self._run(
            "qdbus", "org.kde.plasmashell", "/PlasmaShell",
            "org.kde.PlasmaShell.evaluateScript", script,
        )

    async def _set_xfce(self, path: str) -> bool:
        return await self._run(
            "xfconf-query", "-c", "xfce4-desktop",
            "-p", "/backdrop/screen0/monitoreDP-1/workspace0/last-image",
            "-s", path,
        )

    async def _set_cinnamon(self, uri: str) -> bool:
        return await self._run(
            "gsettings", "set", "org.cinnamon.desktop.background",
            "picture-uri", uri,
        )

    async def _set_mate(self, uri: str) -> bool:
        return await self._run(
            "gsettings", "set", "org.mate.background",
            "picture-filename", uri,
        )

    def get_name(self) -> str:
        return f"Linux ({self._de})"
