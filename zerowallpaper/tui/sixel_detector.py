"""Utility to detect Sixel support in the current terminal."""

import sys
import os

_SIXEL_SUPPORTED = None


def supports_sixel() -> bool:
    """Safely probe the terminal to detect Sixel graphics support.
    
    Returns True ONLY if ZEROWALLPAPER_SIXEL=1 is set in environment.
    Sixel is currently disabled by default due to high terminal load
    and clipboard issues in some Linux terminal emulators.
    """
    global _SIXEL_SUPPORTED
    if _SIXEL_SUPPORTED is not None:
        return _SIXEL_SUPPORTED

    # Check for manual opt-in
    env_force = os.environ.get("ZEROWALLPAPER_SIXEL")
    if env_force == "1":
        _SIXEL_SUPPORTED = True
    else:
        _SIXEL_SUPPORTED = False

    return _SIXEL_SUPPORTED
