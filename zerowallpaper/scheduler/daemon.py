"""Background daemon for ZeroWallpaper auto-change rotation."""

import time
import os
import sys
import signal
from pathlib import Path
from typing import NoReturn

from zerowallpaper.core.config import AppConfig, _get_app_dir
from zerowallpaper.core.playlist import PlaylistManager
from zerowallpaper.platforms.base import get_backend
from zerowallpaper.core.cache import CacheManager


def get_pid_file() -> Path:
    return _get_app_dir() / "daemon.pid"


def is_running() -> int | None:
    pid_file = get_pid_file()
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            # Check if process is still alive
            if sys.platform == "win32":
                import ctypes
                PROCESS_QUERY_INFORMATION = 0x0400
                handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)
                    return pid
            else:
                os.kill(pid, 0)
                return pid
        except (ValueError, ProcessLookupError, PermissionError):
            pid_file.unlink(missing_ok=True)
    return None


def stop_daemon() -> bool:
    pid = is_running()
    if pid:
        try:
            if sys.platform == "win32":
                import subprocess
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
            
            get_pid_file().unlink(missing_ok=True)
            return True
        except Exception:
            return False
    return False


def run_daemon() -> NoReturn:
    """Main daemon loop."""
    # Write PID
    get_pid_file().write_text(str(os.getpid()))
    
    config = AppConfig.load()
    playlist_mgr = PlaylistManager()
    backend = get_backend()
    cache = CacheManager(config)

    while True:
        # Reload config every time to see if interval/enabled changed
        config = AppConfig.load()
        
        if config.auto_change.enabled:
            next_wp_fn = playlist_mgr.get_next()
            if next_wp_fn:
                if cache.is_wallpaper_cached(next_wp_fn):
                    path = cache.get_wallpaper_path(next_wp_fn)
                    try:
                        backend.set_wallpaper(str(path))
                    except Exception:
                        pass # Avoid crashing daemon
            
        # Sleep for the interval
        time.sleep(config.auto_change.interval_minutes * 60)


def start_daemon_detached() -> None:
    """Start the daemon in a detached background process."""
    if is_running():
        return

    import subprocess
    
    # Use the current python interpreter to run ourselves as a daemon
    cmd = [sys.executable, "-m", "zerowallpaper.scheduler.daemon", "--run"]
    
    if sys.platform == "win32":
        # On Windows, use DETACHED_PROCESS to run without a console window
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # On Unix, use a simple Popen which will stay alive after parent exits
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    if "--run" in sys.argv:
        run_daemon()
