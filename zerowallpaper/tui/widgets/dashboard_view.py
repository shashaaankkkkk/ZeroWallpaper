"""Dashboard view for the ZeroWallpaper Command Center."""

from __future__ import annotations

from typing import TYPE_CHECKING
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, Grid
from textual.widget import Widget
from textual.widgets import Static, Label, Button

if TYPE_CHECKING:
    from zerowallpaper.tui.app import ZeroWallpaperApp


from zerowallpaper.tui.widgets.sixel_image import SixelImageWidget

class CurrentWallpaperCard(Widget):
    """Card showing the current desktop wallpaper and its info."""
    
    def compose(self) -> ComposeResult:
        with Vertical(classes="dashboard-card"):
            yield Static(" ╭──── CURRENT WALLPAPER ────╮", classes="card-title-ascii")
            yield Vertical(
                SixelImageWidget(id="dashboard-current-image"),
                id="current-wp-preview-container"
            )
            yield Label("Welcome! Explore to set your first wallpaper", id="current-wp-name", classes="card-subtitle")
            with Horizontal(classes="card-actions"):
                yield Button("[S] Skip Next", id="btn-skip-next", variant="primary")
                yield Button("[V] View HQ", id="btn-view-hq")

class AutoChangeCard(Widget):
    """Card showing auto-changer status and controls."""
    
    def compose(self) -> ComposeResult:
        with Vertical(classes="dashboard-card"):
            yield Static(" ╭──── AUTO-CHANGER ────╮", classes="card-title-ascii")
            yield Label(" ❯ Status:   [b]Stopped[/b]", id="auto-status-label")
            yield Label(" ❯ Interval: 5m", id="auto-interval-label")
            yield Label(" ❯ Timer:    N/A", id="auto-timer-label")
            yield Static(" ──────────────────────────", classes="card-divider")
            with Horizontal(classes="card-actions"):
                yield Button("[A] Start", id="btn-toggle-auto", variant="success")
                yield Button("[I] Interval", id="btn-cycle-interval")

class StatsCard(Widget):
    """Card showing app statistics."""
    
    def compose(self) -> ComposeResult:
        with Vertical(classes="dashboard-card"):
            yield Static(" ╭──── SYSTEM STATS ────╮", classes="card-title-ascii")
            yield Label(" ▣ Total Library: 0", id="stat-total")
            yield Label(" ▣ Cached Files:  0", id="stat-cache")
            yield Label(" ▣ Data Usage:    Moderate", id="stat-usage")
            yield Label(" ▣ Network:       Online", id="stat-net")
            yield Static(" ──────────────────────────", classes="card-divider")

class DashboardView(Widget):
    """The main Dashboard view for the ZeroWallpaper Command Center."""

    def compose(self) -> ComposeResult:
        with Vertical(id="dashboard-scroll"):
            yield Static("""
  ▀▀▀█ █▀▀ █▀▀█ █▀▀█ █   █ █▀▀█ █   █   █▀▀█ █▀▀█ █▀▀█ █▀▀ █▀▀█ 
    █  █▀▀ █▄▄▀ █  █ █▄█▄█ █▄▄█ █   █   █▄▄█ █▄▄█ █▄▄█ █▀▀ █▄▄▀ 
   █▄▄ ▀▀▀ ▀ ▀▀ ▀▀▀▀  ▀ ▀  ▀  ▀ ▀▀▀ ▀▀▀ █    █    █    ▀▀▀ ▀ ▀▀ """, id="dashboard-ascii-logo")
            
            yield Static(" ❯ Z E R O W A L L P A P E R ❮ ", id="dashboard-title-text")
            yield Static(" ❯ COMMAND CENTER CONSOLE ❮ ", id="dashboard-header-sub")
            
            with Vertical(id="dashboard-linear-container"):
                yield CurrentWallpaperCard(id="card-current")
                yield AutoChangeCard(id="card-auto")
                yield StatsCard(id="card-stats")
                
            yield Static("\n [dim i]Shortcuts: [E] Explore  [P] Playlist  [F] Favorites  [M] Manager  [Esc] Back[/dim i]", classes="dashboard-tip")

    def on_mount(self) -> None:
        self.refresh_stats()

    def refresh_stats(self) -> None:
        """Update the dashboard with latest app data."""
        app = self.app
        
        # Update Stats
        self.query_one("#stat-total", Label).update(f" ▣ Total Library: {len(app._search.all_wallpapers)}")
        self.query_one("#stat-cache", Label).update(f" ▣ Cached Files:  {app._cache.get_cached_wallpaper_count()}")
        
        # Update Auto-Changer
        status = "Running" if app._auto_changer.is_running else "Stopped"
        color = "green" if app._auto_changer.is_running else "red"
        self.query_one("#auto-status-label", Label).update(f" ❯ Status:   [{color}]{status}[/{color}]")
        self.query_one("#auto-interval-label", Label).update(f" ❯ Interval: {app._auto_changer.interval_minutes}m")
        self.query_one("#btn-toggle-auto", Button).label = "[A] Stop" if app._auto_changer.is_running else "[A] Start"
        self.query_one("#btn-toggle-auto", Button).variant = "error" if app._auto_changer.is_running else "success"
        
        # Update Current Wallpaper if available
        if hasattr(app, "_last_set_wallpaper") and app._last_set_wallpaper:
            wp = app._last_set_wallpaper
            self.query_one("#current-wp-name", Label).update(f"❯ [b]{wp['filename']}[/b]")
            
            # Show image if cached
            if app._cache.is_wallpaper_cached(wp["filename"]):
                img_path = app._cache.get_wallpaper_path(wp["filename"])
                self.query_one("#dashboard-current-image", SixelImageWidget).set_image(img_path)
            elif app._cache.is_thumbnail_cached(wp["filename"]):
                thumb_path = app._cache.get_thumbnail_path(wp["filename"])
                self.query_one("#dashboard-current-image", SixelImageWidget).set_image(thumb_path)
