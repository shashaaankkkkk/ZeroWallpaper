"""Main ZeroWallpaper Textual TUI application."""

from __future__ import annotations

import asyncio
import random
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Footer, Header, Tabs, Tab, ContentSwitcher
from zerowallpaper.tui.widgets.playlist_manager_view import PlaylistManagerView

from zerowallpaper.core.cache import CacheManager
from zerowallpaper.core.config import AppConfig
from zerowallpaper.core.favorites import FavoritesManager
from zerowallpaper.core.github_api import GitHubFetcher, GitHubAPIError, RateLimitError
from zerowallpaper.core.history import HistoryManager
from zerowallpaper.core.index_builder import IndexBuilder
from zerowallpaper.core.playlist import PlaylistManager
from zerowallpaper.core.search import SearchEngine
from zerowallpaper.tui.playlist_screen import PlaylistScreen
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
from zerowallpaper.tui.screens import HomeScreen


from zerowallpaper.tui.widgets.nav_rail import NavRail, NavRailItem
from zerowallpaper.tui.widgets.dashboard_view import DashboardView


CSS_PATH = Path(__file__).parent / "styles.tcss"


class ZeroWallpaperApp(App):
    """ZeroWallpaper TUI — The Command Center."""

    TITLE = "ZeroWallpaper"
    SUB_TITLE = "Command Center"
    CSS_PATH = CSS_PATH

    BINDINGS = [
        Binding("escape", "back", "Back", show=False),
        Binding("q", "quit", "Quit", show=False),
        Binding("slash", "focus_search", "Search", show=False),
        Binding("s", "set_wallpaper", "Set Wallpaper", show=False),
        Binding("v", "view_image", "View HD Image", show=False),
        Binding("r", "random_wallpaper", "Random", show=False),
        Binding("a", "toggle_auto", "Auto Mode", show=False),
        Binding("f", "toggle_favorite", "Favorite", show=True),
        Binding("p", "toggle_playlist", "Playlist", show=True),
        Binding("i", "change_interval", "Cycle", show=True),
        Binding("m", "manage_playlists", "Manager", show=False),
        Binding("tab", "cycle_focus", "Panel", show=True),
        Binding("R", "refresh_index", "Refresh", show=False),
        Binding("E", "nav_explore", "Explore", show=False),
        Binding("H", "nav_home", "Home", show=False),
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
        self._playlist = PlaylistManager()
        self._auto_changer = AutoChanger(self.config)

        # State
        self._index: dict[str, Any] = {}
        self._current_wallpapers: list[dict[str, Any]] = []
        self._active_query = ""
        self._active_tags: list[str] = []
        self._special_filter = "all"
        self._preview_task: asyncio.Task | None = None
        self._last_set_wallpaper: dict[str, Any] | None = None

        # Platform backend
        try:
            self._backend = get_backend()
        except RuntimeError:
            self._backend = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="root-container"):
            yield NavRail(id="main-nav-rail")
            
            with Vertical(id="content-container"):
                yield SearchBar(id="search-bar")
                
                with ContentSwitcher(initial="view-browser", id="main-content"):
                    with Horizontal(id="view-browser"):
                        yield TagSidebar(id="tag-sidebar")
                        yield WallpaperList(id="wallpaper-list-container")
                        yield PreviewPanel(id="preview-panel")
                    
                    yield PlaylistManagerView(id="view-manager")
                    
                yield StatusBar(id="status-bar-widget")

    async def on_mount(self) -> None:
        """Initialize the app after mounting."""
        # Removed HomeScreen push - start directly in Browse
        
        self._auto_changer.set_callback(self._auto_change_wallpaper)

        # Show loading state
        preview = self.query_one("#preview-panel", PreviewPanel)
        preview.show_placeholder("Loading wallpaper index...")

        # Update status bar
        self._update_status()

        # Load index in background
        self.run_worker(self._load_index(), exclusive=True, name="load_index")
        
        # Clean up old cache files (older than 7 days)
        asyncio.create_task(self._run_cache_cleanup())

    async def _run_cache_cleanup(self) -> None:
        """Run cache cleanup in background."""
        try:
            # Running this in a separate thread/task to ensure UI remains snappy
            loop = asyncio.get_running_loop()
            deleted = await loop.run_in_executor(None, self._cache.cleanup, 1)
            if deleted > 0:
                self.log(f"Cache cleanup: deleted {deleted} old files")
        except Exception:
            pass

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
            
            # Focus the wallpaper list automatically
            wl = self.query_one("#wallpaper-list-container", WallpaperList)
            wl.focus_list()

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
        elif self._special_filter == "playlist":
            playlist_files = set(self._playlist.get_all())
            results = [
                w for w in self._search.all_wallpapers
                if w["filename"] in playlist_files
            ]
            # Maintain playlist order
            order = {fn: i for i, fn in enumerate(self._playlist.get_all())}
            results.sort(key=lambda w: order.get(w["filename"], 999))
        elif self._special_filter == "cached":
            results = [
                w for w in self._search.all_wallpapers
                if self._cache.is_wallpaper_cached(w["filename"])
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
        wl.set_wallpapers(
            results, 
            set(self._favorites.get_all()),
            set(self._playlist.get_all())
        )

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
        status.set_playlist_count(self._playlist.count)
        status.set_cache_count(self._cache.get_cached_wallpaper_count())
        status.set_network("online")
        
        # Also refresh dashboard if visible
        try:
            self.query_one(DashboardView).refresh_stats()
        except Exception:
            pass

    def on_nav_rail_item_rail_item_selected(self, message: NavRailItem.RailItemSelected) -> None:
        """Handle navigation rail selection."""
        content = self.query_one("#main-content", ContentSwitcher)
        
        target = message.screen_id
        if target == "view-playlist":
            content.current = "view-browser"
            self.post_message(TagFilterChanged(active_tags=[], special_filter="playlist"))
        else:
            content.current = target
            
        # Update rail visual state
        self.query_one(NavRail).set_active(message.screen_id)
        
        # Refresh views if needed
        if target == "view-dashboard":
            self.query_one(DashboardView).refresh_stats()
        elif target == "view-manager":
            self.query_one(PlaylistManagerView).refresh_playlists()
        elif target == "view-browser":
            self.post_message(TagFilterChanged(active_tags=[], special_filter="all"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks from the Dashboard and other views."""
        button_id = event.button.id
        
        if button_id == "btn-skip-next":
            self.run_worker(self._auto_change_wallpaper(), exclusive=True, name="skip_next")
            self.notify("Switching to next wallpaper...", title="⚡ Skip")
        elif button_id == "btn-view-hq":
            self.action_view_image()
        elif button_id == "btn-toggle-auto":
            self.action_toggle_auto()
        elif button_id == "btn-cycle-interval":
            self.action_change_interval()
        elif button_id == "btn-set-wp":
            self.action_set_wallpaper()
        elif button_id == "btn-add-playlist":
            self._action_add_to_playlist()
        elif button_id == "btn-toggle-fav":
            self._action_toggle_favorite()

    def _action_add_to_playlist(self) -> None:
        """Show playlist selection screen."""
        from zerowallpaper.tui.screens import PlaylistSelectionScreen
        wp = self.query_one(WallpaperList).get_current_wallpaper()
        if not wp:
            return

        playlists = self._playlist.playlist_names
        filename = wp["filename"]
        
        def on_playlist_chosen(choice: str | None) -> None:
            if not choice:
                return
            if choice == "--create-new--":
                # Implementation of Create Playlist from the modal choice
                def on_name_submitted(name: str | None) -> None:
                    if name and name.strip():
                        self._playlist.create_playlist(name.strip())
                        self._playlist.add(filename, name.strip())
                        self.notify(f"Created & Added to {name}", title="[PL] Playlist")
                        self.query_one(PreviewPanel).show_preview(None, wp, is_in_playlist=True)
                
                from zerowallpaper.tui.screens import InputScreen
                self.push_screen(InputScreen("Create New Playlist", "Playlist Name"), on_name_submitted)
                return
            
            self._playlist.add(filename, choice)
            self.notify(f"Added to {choice}", title="[PL] Playlist Updated")
            self.query_one(PreviewPanel).show_preview(None, wp, is_in_playlist=True)

        self.push_screen(PlaylistSelectionScreen(playlists), on_playlist_chosen)

    def _action_toggle_favorite(self) -> None:
        """Toggle favorite status for current wallpaper."""
        wp = self.query_one(WallpaperList).get_current_wallpaper()
        if not wp:
            return
        # TODO: Implement favorites in PlaylistManager or separate FavoriteManager
        self.notify("Added to Favorites", title="[*] Saved")

    # --- Message Handlers ---

    def on_search_changed(self, event: SearchChanged) -> None:
        """Handle search query changes."""
        self._active_query = event.query
        self._apply_filters()
        # Switch to browser view if user searches
        self.query_one("#main-content", ContentSwitcher).current = "view-browser"
        self.query_one(NavRail).set_active("view-browser")

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
        """Handle wallpaper highlight to update preview."""
        wp = event.wallpaper
        filename = wp["filename"]
        
        if self._preview_task and not self._preview_task.done():
            self._preview_task.cancel()

        # Instantly clear the old preview if not cached
        if not self._cache.is_thumbnail_cached(filename) and not self._cache.is_wallpaper_cached(filename):
            self.query_one("#preview-panel", PreviewPanel).show_loading()

        self._preview_task = asyncio.create_task(
            self._debounced_load_preview(wp)
        )

    async def _debounced_load_preview(self, wallpaper: dict[str, Any]) -> None:
        """Wait a moment before loading preview to avoid flooding during scrolling."""
        try:
            await asyncio.sleep(0.15)
            await self._load_preview(wallpaper)
        except asyncio.CancelledError:
            pass

    def on_wallpaper_activated(self, event: WallpaperActivated) -> None:
        """Handle wallpaper activation (Enter) — set as wallpaper."""
        self.action_set_wallpaper()

    async def _load_preview(self, wallpaper: dict[str, Any]) -> None:
        """Load and display wallpaper preview."""
        preview = self.query_one("#preview-panel", PreviewPanel)
        filename = wallpaper["filename"]
        is_in = self._playlist.is_in_playlist(filename)

        # Check thumbnail cache first
        if self._cache.is_thumbnail_cached(filename):
            thumb_path = self._cache.get_thumbnail_path(filename)
            preview.show_cached_preview(thumb_path, wallpaper, is_in_playlist=is_in)
            return

        # Check wallpaper cache
        if self._cache.is_wallpaper_cached(filename):
            wp_path = self._cache.get_wallpaper_path(filename)
            preview.show_cached_preview(wp_path, wallpaper, is_in_playlist=is_in)
            return

        # Download for preview
        preview.show_loading()
        try:
            image_data = await self._fetcher.download_image(filename)

            # Save as thumbnail for future fast loads
            try:
                from PIL import Image
                from io import BytesIO
                img = Image.open(BytesIO(image_data))
                img = img.convert("RGB")
                img.thumbnail((800, 800), Image.LANCZOS)
                buf = BytesIO()
                img.save(buf, format="PNG")
                self._cache.save_thumbnail(filename, buf.getvalue())
            except Exception:
                pass

            preview.show_preview(image_data, wallpaper, is_in_playlist=is_in)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            preview.show_placeholder(f"Preview failed\n{str(e)[:30]}")

    async def _set_wallpaper(self, wallpaper: dict[str, Any]) -> None:
        """Download (if needed) and set a wallpaper."""
        self._last_set_wallpaper = wallpaper
        filename = wallpaper["filename"]

        # Download if not cached
        if not self._cache.is_wallpaper_cached(filename):
            self.notify("Downloading wallpaper...", title="[DOWN] Download")
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
                    title="[OK] Wallpaper Applied",
                    severity="information",
                )
                self._update_status()
                # Refresh dashboard if it exists
                try:
                    from zerowallpaper.tui.widgets.dashboard_view import DashboardView
                    self.query_one(DashboardView).refresh_stats()
                except Exception:
                    pass
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
        """Callback for auto-changer to pick and set a wallpaper.
        
        Prioritizes the user's playlist, then falls back to current view.
        """
        # 1. Try playlist first
        next_fn = self._playlist.get_next()
        wp = None
        
        if next_fn:
            # Find wallpaper dict for this filename
            wp = next((w for w in self._search.all_wallpapers if w["filename"] == next_fn), None)
        
        # 2. Fallback to random choice from current wallpapers
        if not wp and self._current_wallpapers:
            wp = random.choice(self._current_wallpapers)
            
        if wp:
            # Attempt to set wallpaper, if it fails (offline), _set_wallpaper will notify
            # and we just wait for the next cycle.
            await self._set_wallpaper(wp)
            
            # 3. Pre-fetch upcoming items in the playlist
            self.run_worker(self._prefetch_upcoming(), exclusive=False, name="prefetch")

    async def _prefetch_upcoming(self) -> None:
        """Download the next 2-3 wallpapers in the playlist to ensure they are ready."""
        upcoming = self._playlist.peek_upcoming(3)
        for fn in upcoming:
            if not self._cache.is_wallpaper_cached(fn):
                try:
                    wp = next((w for w in self._search.all_wallpapers if w["filename"] == fn), None)
                    if wp:
                        data = await self._fetcher.download_image(fn)
                        self._cache.save_wallpaper(fn, data)
                except Exception:
                    pass  # Silently fail pre-fetch

    # --- Actions ---

    def action_back(self) -> None:
        """Universal back navigation."""
        content = self.query_one("#main-content", ContentSwitcher)
        if content.current != "view-dashboard":
            self.action_nav_home()
        else:
            # If already on home, maybe clear search
            sb = self.query_one("#search-bar", SearchBar)
            if self._active_query:
                sb.set_query("")
            else:
                # Show home screen if completely at root
                self.push_screen(HomeScreen())

    def action_focus_search(self) -> None:
        """Focus the search bar."""
        sb = self.query_one("#search-bar", SearchBar)
        sb.focus_input()

    def action_set_wallpaper(self) -> None:
        """Set the currently highlighted wallpaper."""
        wp = self.query_one(WallpaperList).get_current_wallpaper()
        if wp:
            self.run_worker(
                self._set_wallpaper(wp),
                exclusive=False,
                name="set_wallpaper",
            )
        else:
            self.notify("No wallpaper selected", severity="warning")

    def action_nav_home(self) -> None:
        """Navigate to Dashboard via shortcut."""
        content = self.query_one("#main-content", ContentSwitcher)
        content.current = "view-dashboard"
        self.query_one(NavRail).set_active("view-dashboard")
        self.query_one(DashboardView).refresh_stats()

    def action_nav_explore(self) -> None:
        """Navigate to Explore view via shortcut."""
        content = self.query_one("#main-content", ContentSwitcher)
        content.current = "view-browser"
        self.query_one(NavRail).set_active("view-browser")
        self.post_message(TagFilterChanged(active_tags=[], special_filter="all"))

    def action_nav_playlist(self) -> None:
        """Navigate to Playlist view via shortcut."""
        content = self.query_one("#main-content", ContentSwitcher)
        content.current = "view-browser"
        self.query_one(NavRail).set_active("view-browser")
        self.post_message(TagFilterChanged(active_tags=[], special_filter="playlist"))

    def action_nav_favorites(self) -> None:
        """Navigate to Favorites view via shortcut."""
        content = self.query_one("#main-content", ContentSwitcher)
        content.current = "view-browser"
        self.query_one(NavRail).set_active("view-browser")
        self.post_message(TagFilterChanged(active_tags=[], special_filter="favorites"))

    def action_view_image(self) -> None:
        """View the high-resolution image using macOS QuickLook."""
        wl = self.query_one("#wallpaper-list-container", WallpaperList)
        wp = wl.get_current_wallpaper()
        if not wp:
            return
            
        filename = wp["filename"]
        
        wp_path = None
        if self._cache.is_wallpaper_cached(filename):
            wp_path = self._cache.get_wallpaper_path(filename)
        elif self._cache.is_thumbnail_cached(filename):
            wp_path = self._cache.get_thumbnail_path(filename)
            
        if wp_path:
            import subprocess
            import sys
            import os
            try:
                if sys.platform == "win32":
                    os.startfile(wp_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(wp_path)], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(["xdg-open", str(wp_path)], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                self.notify(f"Failed to open image: {e}", severity="error")
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
                title="[AUTO] Mode ON",
            )
        else:
            self.notify("Auto-change stopped", title="[OFF] Mode OFF")
        self._update_status()

    def action_change_interval(self) -> None:
        """Cycle auto-change interval."""
        intervals = [1, 5, 10, 30, 60]
        current = self._auto_changer.interval_minutes
        try:
            idx = intervals.index(current)
            next_interval = intervals[(idx + 1) % len(intervals)]
        except ValueError:
            next_interval = 5
            
        self._auto_changer.set_interval(next_interval)
        self.notify(
            f"Interval set to {next_interval} minutes",
            title="[TIME] Timer Updated"
        )
        self._update_status()

    def action_toggle_favorite(self) -> None:
        """Toggle favorite on current wallpaper."""
        wl = self.query_one("#wallpaper-list-container", WallpaperList)
        wp = wl.get_current_wallpaper()
        if wp:
            is_fav = self._favorites.toggle(wp["filename"])
            if is_fav:
                self.notify(f"[*] Added to favorites", title=wp["filename"])
            else:
                self.notify(f"[ ] Removed from favorites", title=wp["filename"])
            # Refresh list to update fav indicators
            self._apply_filters()

    def action_toggle_playlist(self) -> None:
        """Add wallpaper to chosen playlist."""
        self._action_add_to_playlist()

    def action_manage_playlists(self) -> None:
        """Open the Playlist Management view."""
        content = self.query_one("#main-content", ContentSwitcher)
        content.current = "view-manager"
        self.query_one(NavRail).set_active("view-manager")
        self.query_one(PlaylistManagerView).refresh_playlists()

    def action_cycle_focus(self) -> None:
        """Cycle focus between panels."""
        self.screen.focus_next()

    def action_refresh_index(self) -> None:
        """Force refresh the wallpaper index."""
        self.notify("Refreshing index...", title="[REFRESH] Index")
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
