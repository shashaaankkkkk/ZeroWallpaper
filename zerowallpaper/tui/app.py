"""Main ZeroWallpaper Textual TUI application."""

from __future__ import annotations

import asyncio
import random
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Footer, Header

from zerowallpaper.core.cache import CacheManager
from zerowallpaper.core.config import AppConfig
from zerowallpaper.core.favorites import FavoritesManager
from zerowallpaper.core.github_api import GitHubFetcher, GitHubAPIError, RateLimitError
from zerowallpaper.core.history import HistoryManager
from zerowallpaper.core.index_builder import IndexBuilder
from zerowallpaper.core.search import SearchEngine
from zerowallpaper.platforms.base import get_backend
from zerowallpaper.scheduler.auto_changer import AutoChanger
from zerowallpaper.tui.widgets.preview_panel import PreviewPanel
from zerowallpaper.tui.widgets.search_bar import SearchBar, SearchChanged
from zerowallpaper.tui.widgets.status_bar import StatusBar
from zerowallpaper.tui.widgets.tag_sidebar import TagSidebar, TagFilterChanged
from zerowallpaper.tui.widgets.wallpaper_list import (
    WallpaperList,
    WallpaperSelected,
    WallpaperActivated,
)


CSS_PATH = Path(__file__).parent / "styles.tcss"


class ZeroWallpaperApp(App):
    """Premium terminal wallpaper browser and manager."""

    TITLE = "ZeroWallpaper"
    SUB_TITLE = "Aesthetic Wallpaper Manager"
    CSS_PATH = CSS_PATH

    BINDINGS = [
        Binding("q", "quit", "Quit", show=False),
        Binding("slash", "focus_search", "Search", show=False),
        Binding("s", "set_wallpaper", "Set Wallpaper", show=False),
        Binding("v", "view_image", "View HD Image", show=False),
        Binding("r", "random_wallpaper", "Random", show=False),
        Binding("a", "toggle_auto", "Auto Mode", show=False),
        Binding("f", "toggle_favorite", "Favorite", show=False),
        Binding("tab", "cycle_focus", "Switch Panel", show=False),
        Binding("R", "refresh_index", "Refresh", show=False),
    ]

    def __init__(
        self,
        config: AppConfig | None = None,
        rebuild_index: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.config = config or AppConfig.load()
        self._rebuild_index = rebuild_index

        # Core modules
        self._fetcher = GitHubFetcher(token=self.config.github_token)
        self._cache = CacheManager(self.config)
        self._index_builder = IndexBuilder(self._fetcher, self._cache)
        self._search = SearchEngine()
        self._favorites = FavoritesManager()
        self._history = HistoryManager()
        self._auto_changer = AutoChanger(self.config)

        # State
        self._index: dict[str, Any] = {}
        self._current_wallpapers: list[dict[str, Any]] = []
        self._active_query = ""
        self._active_tags: list[str] = []
        self._special_filter = "all"
        self._preview_task: asyncio.Task | None = None

        # Platform backend
        try:
            self._backend = get_backend()
        except RuntimeError:
            self._backend = None

    def compose(self) -> ComposeResult:
        yield SearchBar(id="search-bar")
        with Horizontal(id="main-panels"):
            yield TagSidebar(id="tag-sidebar")
            yield WallpaperList(id="wallpaper-list-container")
            yield PreviewPanel(id="preview-panel")
        yield StatusBar(id="status-bar-widget")

    async def on_mount(self) -> None:
        """Initialize the app after mounting."""
        self._auto_changer.set_callback(self._auto_change_wallpaper)

        # Show loading state
        preview = self.query_one("#preview-panel", PreviewPanel)
        preview.show_placeholder("Loading wallpaper index...")

        # Update status bar
        self._update_status()

        # Load index in background
        self.run_worker(self._load_index(), exclusive=True, name="load_index")

    async def _load_index(self) -> None:
        """Load or build the wallpaper index."""
        try:
            self._index = await self._index_builder.build_index(
                force=self._rebuild_index
            )
            self._search.load_index(self._index)

            # Populate UI
            self._populate_tags()
            self._apply_filters()
            self._update_status()

            count = self._index.get("wallpaper_count", 0)
            self.notify(
                f"Loaded {count} wallpapers",
                title="Index Ready",
                severity="information",
            )

        except RateLimitError as e:
            self.notify(str(e), title="Rate Limited", severity="error")
            preview = self.query_one("#preview-panel", PreviewPanel)
            preview.show_placeholder("Rate limited!\nSet GITHUB_TOKEN")

        except GitHubAPIError as e:
            self.notify(str(e), title="API Error", severity="error")
            # Try loading from stale cache
            cached = self._cache.get_index()
            if cached:
                self._index = cached
                self._search.load_index(self._index)
                self._populate_tags()
                self._apply_filters()
                self.notify(
                    "Using cached index (may be outdated)",
                    severity="warning",
                )
            else:
                preview = self.query_one("#preview-panel", PreviewPanel)
                preview.show_placeholder("Failed to load index\nCheck network")

        except Exception as e:
            self.notify(f"Error: {e}", title="Error", severity="error")

    def _populate_tags(self) -> None:
        """Populate tag sidebar from loaded index."""
        tags = self._index.get("tags", {})
        sidebar = self.query_one("#tag-sidebar", TagSidebar)
        sidebar.set_tags(tags)

    def _apply_filters(self) -> None:
        """Apply current filters and update wallpaper list."""
        if self._special_filter == "favorites":
            fav_files = set(self._favorites.get_all())
            results = [
                w for w in self._search.all_wallpapers
                if w["filename"] in fav_files
            ]
        elif self._special_filter == "recent":
            recent_files = self._history.get_recent(50)
            recent_set = set(recent_files)
            results = [
                w for w in self._search.all_wallpapers
                if w["filename"] in recent_set
            ]
            # Sort by recent order
            order = {fn: i for i, fn in enumerate(recent_files)}
            results.sort(key=lambda w: order.get(w["filename"], 999))
        else:
            results = self._search.combined_filter(
                query=self._active_query,
                tags=self._active_tags if self._active_tags else None,
            )

        self._current_wallpapers = results

        # Update wallpaper list
        wl = self.query_one("#wallpaper-list-container", WallpaperList)
        wl.set_wallpapers(results, set(self._favorites.get_all()))

        # Update search bar counts
        sb = self.query_one("#search-bar", SearchBar)
        sb.set_counts(len(results), self._search.total_count)

        # Update status
        self._update_status()

    def _update_status(self) -> None:
        """Update the status bar."""
        status = self.query_one("#status-bar-widget", StatusBar)

        if self._auto_changer.is_running:
            status.set_mode(f"Auto ({self._auto_changer.interval_minutes}m)")
        else:
            status.set_mode("Manual")

        status.set_filter_count(len(self._active_tags))
        status.set_cache_count(self._cache.get_cached_wallpaper_count())
        status.set_network("online")

    # --- Message Handlers ---

    def on_search_changed(self, event: SearchChanged) -> None:
        """Handle search query changes."""
        self._active_query = event.query
        self._apply_filters()

    def on_tag_filter_changed(self, event: TagFilterChanged) -> None:
        """Handle tag filter changes."""
        if event.special_filter:
            self._special_filter = event.special_filter
            self._active_tags = []
        else:
            self._special_filter = "all"
            self._active_tags = event.active_tags

            # Clear special filter selection
            sidebar = self.query_one("#tag-sidebar", TagSidebar)
            sidebar.clear_special_selection()

        self._apply_filters()

    def on_wallpaper_selected(self, event: WallpaperSelected) -> None:
        """Handle wallpaper highlight — load preview."""
        if self._preview_task and not self._preview_task.done():
            self._preview_task.cancel()

        self._preview_task = asyncio.create_task(
            self._load_preview(event.wallpaper)
        )

    def on_wallpaper_activated(self, event: WallpaperActivated) -> None:
        """Handle wallpaper activation (Enter) — preview only, don't set."""
        # Enter just ensures preview is loaded (same as highlight)
        if self._preview_task and not self._preview_task.done():
            self._preview_task.cancel()
        self._preview_task = asyncio.create_task(
            self._load_preview(event.wallpaper)
        )
        self.notify(
            "Press 's' to set as wallpaper",
            title=event.wallpaper["filename"],
            severity="information",
        )

    async def _load_preview(self, wallpaper: dict[str, Any]) -> None:
        """Load and display wallpaper preview."""
        preview = self.query_one("#preview-panel", PreviewPanel)
        filename = wallpaper["filename"]

        # Check thumbnail cache first
        if self._cache.is_thumbnail_cached(filename):
            thumb_path = self._cache.get_thumbnail_path(filename)
            preview.show_cached_preview(thumb_path, wallpaper)
            return

        # Check wallpaper cache
        if self._cache.is_wallpaper_cached(filename):
            wp_path = self._cache.get_wallpaper_path(filename)
            preview.show_cached_preview(wp_path, wallpaper)
            return

        # Download for preview
        preview.show_loading()
        try:
            image_data = await self._fetcher.download_image(filename)

            # Save as thumbnail
            try:
                from PIL import Image
                from io import BytesIO
                img = Image.open(BytesIO(image_data))
                img = img.convert("RGB")
                # Create thumbnail (high-res for sharp terminal preview)
                img.thumbnail((800, 800), Image.LANCZOS)
                buf = BytesIO()
                img.save(buf, format="PNG")
                self._cache.save_thumbnail(filename, buf.getvalue())
            except Exception:
                pass

            preview.show_preview(image_data, wallpaper)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            preview.show_placeholder(f"Preview failed\n{str(e)[:30]}")

    async def _set_wallpaper(self, wallpaper: dict[str, Any]) -> None:
        """Download (if needed) and set a wallpaper."""
        filename = wallpaper["filename"]

        # Download if not cached
        if not self._cache.is_wallpaper_cached(filename):
            self.notify("Downloading wallpaper...", title="⬇️ Download")
            try:
                data = await self._fetcher.download_image(filename)
                self._cache.save_wallpaper(filename, data)
            except Exception as e:
                self.notify(f"Download failed: {e}", severity="error")
                return

        wp_path = self._cache.get_wallpaper_path(filename)

        if self._backend:
            success = await self._backend.set_wallpaper(wp_path)
            if success:
                self._history.add(filename)
                self.notify(
                    f"Set: {filename}",
                    title="✓ Wallpaper Applied",
                    severity="information",
                )
                self._update_status()
            else:
                self.notify(
                    "Failed to set wallpaper",
                    severity="error",
                )
        else:
            self.notify(
                "No wallpaper backend available",
                severity="warning",
            )

    async def _auto_change_wallpaper(self) -> None:
        """Callback for auto-changer to pick and set a random wallpaper."""
        if not self._current_wallpapers:
            return

        wp = random.choice(self._current_wallpapers)
        await self._set_wallpaper(wp)

    # --- Actions ---

    def action_focus_search(self) -> None:
        """Focus the search bar."""
        sb = self.query_one("#search-bar", SearchBar)
        sb.focus_input()

    def action_set_wallpaper(self) -> None:
        """Set the currently selected wallpaper (s key)."""
        wl = self.query_one("#wallpaper-list-container", WallpaperList)
        wp = wl.get_current_wallpaper()
        if wp:
            self.run_worker(
                self._set_wallpaper(wp),
                exclusive=False,
                name="set_wallpaper",
            )
        else:
            self.notify("No wallpaper selected", severity="warning")

    def action_view_image(self) -> None:
        """View the high-resolution image using macOS QuickLook."""
        wl = self.query_one("#wallpaper-list-container", WallpaperList)
        wp = wl.get_current_wallpaper()
        if not wp:
            return
            
        filename = wp["filename"]
        if self._cache.is_wallpaper_cached(filename):
            wp_path = self._cache.get_wallpaper_path(filename)
            import subprocess
            subprocess.Popen(["qlmanage", "-p", str(wp_path)], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            self.notify("Please wait for preview to download first", severity="warning")

    def action_random_wallpaper(self) -> None:
        """Set a random wallpaper from current list."""
        if self._current_wallpapers:
            wp = random.choice(self._current_wallpapers)
            self.run_worker(
                self._set_wallpaper(wp),
                exclusive=False,
                name="random_wallpaper",
            )

    def action_toggle_auto(self) -> None:
        """Toggle auto-change mode."""
        running = self._auto_changer.toggle()
        if running:
            self.notify(
                f"Auto-change every {self._auto_changer.interval_minutes}m",
                title="⚡ Auto Mode ON",
            )
        else:
            self.notify("Auto-change stopped", title="◈ Auto Mode OFF")
        self._update_status()

    def action_toggle_favorite(self) -> None:
        """Toggle favorite on current wallpaper."""
        wl = self.query_one("#wallpaper-list-container", WallpaperList)
        wp = wl.get_current_wallpaper()
        if wp:
            is_fav = self._favorites.toggle(wp["filename"])
            if is_fav:
                self.notify(f"★ Added to favorites", title=wp["filename"])
            else:
                self.notify(f"☆ Removed from favorites", title=wp["filename"])
            # Refresh list to update fav indicators
            self._apply_filters()

    def action_cycle_focus(self) -> None:
        """Cycle focus between panels."""
        self.screen.focus_next()

    def action_refresh_index(self) -> None:
        """Force refresh the wallpaper index."""
        self.notify("Refreshing index...", title="🔄 Refresh")
        self.run_worker(self._refresh_index(), exclusive=True, name="refresh")

    async def _refresh_index(self) -> None:
        """Refresh the index from GitHub."""
        try:
            self._index = await self._index_builder.refresh_index()
            self._search.load_index(self._index)
            self._populate_tags()
            self._apply_filters()
            count = self._index.get("wallpaper_count", 0)
            self.notify(f"Refreshed: {count} wallpapers", severity="information")
        except Exception as e:
            self.notify(f"Refresh failed: {e}", severity="error")

    async def on_unmount(self) -> None:
        """Cleanup on app exit."""
        self._auto_changer.stop()
        await self._fetcher.close()
