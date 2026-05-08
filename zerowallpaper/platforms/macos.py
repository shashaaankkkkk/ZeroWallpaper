"""macOS wallpaper setter using osascript."""

from __future__ import annotations

import asyncio
from pathlib import Path

from zerowallpaper.platforms.base import WallpaperBackend


class MacOSBackend(WallpaperBackend):
    """Set wallpaper on macOS using AppleScript via osascript.

    Uses multiple approaches with fallback:
    1. Finder 'set desktop picture' (most reliable on macOS 14+)
    2. System Events 'tell every desktop' (older macOS)
    3. NSWorkspace via Python/ObjC bridge (if available)
    """

    async def set_wallpaper(self, image_path: Path) -> bool:
        abs_path = str(image_path.resolve())

        # Ensure the file is in a macOS-compatible format
        abs_path = await self._ensure_compatible_format(abs_path)

        # Method 1: Swift Bridge (Most robust, bypasses many permission issues)
        if await self._set_via_swift_bridge(abs_path):
            return True

        # Method 2: Finder (reliable fallback)
        if await self._set_via_finder(abs_path):
            return True

        # Method 3: System Events (fallback for older macOS)
        if await self._set_via_system_events(abs_path):
            return True

        # Method 4: sqlite + killall Dock (last resort)
        if await self._set_via_sqlite(abs_path):
            return True

        return False

    async def _set_via_swift_bridge(self, abs_path: str) -> bool:
        """Set wallpaper using a small Swift script via the CLI.
        
        This uses the native NSWorkspace API which is more reliable than 
        AppleScript on modern macOS.
        """
        script = f"""
import AppKit
let url = URL(fileURLWithPath: "{abs_path}")
try? NSWorkspace.shared.setDesktopImageURL(url, for: NSScreen.main!, options: [:])
"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "swift", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False

    async def _set_via_finder(self, abs_path: str) -> bool:
        """Set wallpaper using Finder (works on macOS 14+)."""
        script = (
            'tell application "Finder" to '
            f'set desktop picture to POSIX file "{abs_path}"'
        )
        return await self._run_osascript(script)

    async def _set_via_system_events(self, abs_path: str) -> bool:
        """Set wallpaper using System Events."""
        script = (
            'tell application "System Events" to '
            'tell every desktop to '
            f'set picture to POSIX file "{abs_path}"'
        )
        return await self._run_osascript(script)

    async def _set_via_sqlite(self, abs_path: str) -> bool:
        """Set wallpaper by directly modifying the desktoppicture database.

        This is a last-resort fallback that works when AppleScript
        permissions are denied.
        """
        import os
        db_path = os.path.expanduser(
            "~/Library/Application Support/Dock/desktoppicture.db"
        )
        if not os.path.exists(db_path):
            return False

        try:
            # Update the database
            proc = await asyncio.create_subprocess_exec(
                "sqlite3", db_path,
                f"UPDATE data SET value = '{abs_path}';",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                return False

            # Restart Dock to apply
            proc = await asyncio.create_subprocess_exec(
                "killall", "Dock",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return True
        except Exception:
            return False

    async def _run_osascript(self, script: str) -> bool:
        """Execute an osascript command."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False

    async def _ensure_compatible_format(self, abs_path: str) -> str:
        """Convert .webp images to .png since macOS doesn't support
        webp as wallpaper natively in all versions."""
        if not abs_path.lower().endswith(".webp"):
            return abs_path

        try:
            from PIL import Image
            png_path = abs_path.rsplit(".", 1)[0] + ".png"

            # Skip if already converted
            if Path(png_path).exists():
                return png_path

            img = Image.open(abs_path)
            img.save(png_path, "PNG")
            return png_path
        except Exception:
            return abs_path

    def get_name(self) -> str:
        return "macOS (osascript)"
