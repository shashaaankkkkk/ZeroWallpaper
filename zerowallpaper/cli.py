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

    # Import here to avoid slow startup for --help/--version
    from zerowallpaper.core.config import AppConfig

    config = AppConfig.load()

    if args.token:
        config.github_token = args.token
        config.save()

    # Launch the TUI
    from zerowallpaper.tui.app import ZeroWallpaperApp

    app = ZeroWallpaperApp(
        config=config,
        rebuild_index=args.rebuild_index,
    )
    app.run()


if __name__ == "__main__":
    main()
