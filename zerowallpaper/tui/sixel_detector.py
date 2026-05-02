"""Utility to detect Sixel support in the current terminal."""

import sys
import os

_SIXEL_SUPPORTED = None


def supports_sixel() -> bool:
    """Safely probe the terminal to detect Sixel graphics support.
    
    Returns True if the terminal responds with Sixel capability (4),
    otherwise False. Results are cached.
    """
    global _SIXEL_SUPPORTED
    if _SIXEL_SUPPORTED is not None:
        return _SIXEL_SUPPORTED

    # Check for manual override
    env_force = os.environ.get("ZEROWALLPAPER_SIXEL")
    if env_force == "1":
        _SIXEL_SUPPORTED = True
        return True
    elif env_force == "0":
        _SIXEL_SUPPORTED = False
        return False

    # Standard sanity checks
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        _SIXEL_SUPPORTED = False
        return False

    if sys.platform == "win32":
        # Standard Windows Console doesn't support Sixel natively
        _SIXEL_SUPPORTED = False
        return False

    try:
        import select
        import termios
        import tty
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            # Set to cbreak mode to read individual characters without echoing
            tty.setcbreak(fd)
            # Send Primary Device Attributes request
            sys.stdout.write("\033[c")
            sys.stdout.flush()

            response = ""
            while True:
                # Wait up to 0.1s for input to avoid hanging
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not r:
                    break
                char = sys.stdin.read(1)
                response += char
                if char == "c":
                    break
            
            # Example response: \x1b[?62;c (no Sixel) or \x1b[?1;2;4;c (Sixel supported)
            # The '4' parameter in the DA response indicates Sixel support.
            if response.startswith("\033[?") and "c" in response:
                params = response[3:-1].split(";")
                _SIXEL_SUPPORTED = "4" in params
            else:
                _SIXEL_SUPPORTED = False

        finally:
            # Always restore terminal settings!
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    except Exception:
        # If anything fails (e.g., termios not available, IO error), assume False
        _SIXEL_SUPPORTED = False

    return _SIXEL_SUPPORTED
