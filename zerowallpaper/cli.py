"""CLI entry point for ZeroWallpaper."""

from __future__ import annotations

import argparse
import sys

from zerowallpaper import __version__, __app_name__


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="zerowallpaper",
        description="Premium terminal wallpaper browser and manager",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"{__app_name__} {__version__}",
    )
    parser.add_argument(
        "--rebuild-index", action="store_true",
        help="Force rebuild the wallpaper index from GitHub",
    )
    parser.add_argument(
        "--token", type=str, default="",
        help="GitHub API token for higher rate limits",
    )

    args = parser.parse_args()

    # Launch the TUI or handle subcommands
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        from zerowallpaper.scheduler import daemon
        if len(sys.argv) > 2:
            cmd = sys.argv[2]
            if cmd == "start":
                if daemon.is_running():
                    print("Daemon is already running.")
                else:
                    daemon.start_daemon_detached()
                    print("ZeroWallpaper daemon started in background.")
            elif cmd == "stop":
                if daemon.stop_daemon():
                    print("ZeroWallpaper daemon stopped.")
                else:
                    print("Daemon is not running.")
            elif cmd == "status":
                pid = daemon.is_running()
                if pid:
                    print(f"Daemon is running (PID: {pid})")
                else:
                    print("Daemon is not running.")
            else:
                print("Usage: zerowallpaper daemon [start|stop|status]")
        else:
            print("Usage: zerowallpaper daemon [start|stop|status]")
        return

    from zerowallpaper.core.config import AppConfig
    config = AppConfig.load()

    if args.token:
        config.github_token = args.token
        config.save()

    from zerowallpaper.tui.app import ZeroWallpaperApp

    app = ZeroWallpaperApp(
        config=config,
        rebuild_index=args.rebuild_index,
    )
    app.run()


if __name__ == "__main__":
    main()
