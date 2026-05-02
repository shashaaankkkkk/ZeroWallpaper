"""Wallpaper list widget for browsing wallpapers."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, ListView, ListItem, Label


def clean_filename(filename: str) -> str:
    """Convert a filename to a human-readable name."""
    stem = Path(filename).stem
    # Replace separators with spaces
    name = re.sub(r'[-_]+', ' ', stem)
    # Capitalize each word
    name = name.title()
    # Clean up multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def format_size(size_bytes: int) -> str:
    """Format bytes into a human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def format_tags(tags: list[str], max_tags: int = 4) -> str:
    """Format tags as badge string."""
    if not tags:
        return ""
    shown = tags[:max_tags]
    tag_str = " ".join(f"[{t}]" for t in shown)
    if len(tags) > max_tags:
        tag_str += f" +{len(tags) - max_tags}"
    return tag_str


class WallpaperSelected(Message):
    """Posted when a wallpaper is highlighted/selected."""

    def __init__(self, wallpaper: dict[str, Any]) -> None:
        super().__init__()
        self.wallpaper = wallpaper


class WallpaperActivated(Message):
    """Posted when a wallpaper is activated (Enter pressed)."""

    def __init__(self, wallpaper: dict[str, Any]) -> None:
        super().__init__()
        self.wallpaper = wallpaper


class WallpaperListItem(ListItem):
    """Single wallpaper entry in the list."""

    def __init__(
        self, wallpaper: dict[str, Any], is_fav: bool = False, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.wallpaper = wallpaper
        self.is_fav = is_fav
        self.add_class("wallpaper-item")

    def compose(self) -> ComposeResult:
        name = clean_filename(self.wallpaper["filename"])
        tags = format_tags(self.wallpaper.get("tags", []))
        fav = " ★" if self.is_fav else ""

        yield Static(f" ▸ {name}{fav}", classes="wp-name")
        if tags:
            yield Static(f"    {tags}", classes="wp-tags")


class WallpaperList(Widget):
    """Scrollable list of wallpapers with keyboard navigation."""

    BINDINGS = [
        ("enter", "activate_wallpaper", "Set Wallpaper"),
    ]

    current_index = reactive(-1)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._wallpapers: list[dict[str, Any]] = []
        self._favorites: set[str] = set()
        self._list_view: ListView | None = None

    def compose(self) -> ComposeResult:
        yield Static(" ◆ WALLPAPERS", classes="panel-title")
        yield ListView(id="wallpaper-list")

    def on_mount(self) -> None:
        self._list_view = self.query_one("#wallpaper-list", ListView)

    def set_wallpapers(
        self, wallpapers: list[dict[str, Any]], favorites: set[str] | None = None
    ) -> None:
        """Update the wallpaper list."""
        self._wallpapers = wallpapers
        if favorites is not None:
            self._favorites = favorites

        lv = self.query_one("#wallpaper-list", ListView)
        lv.clear()

        for wp in wallpapers:
            is_fav = wp["filename"] in self._favorites
            item = WallpaperListItem(wp, is_fav=is_fav)
            lv.append(item)

        # Select first item if available
        if wallpapers and lv.children:
            lv.index = 0

    def set_favorites(self, favorites: set[str]) -> None:
        """Update favorites set and refresh display."""
        self._favorites = favorites

    def action_activate_wallpaper(self) -> None:
        """Handle explicit Enter key to set wallpaper."""
        wp = self.get_current_wallpaper()
        if wp:
            self.post_message(WallpaperActivated(wp))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle item highlight change."""
        if event.item and isinstance(event.item, WallpaperListItem):
            self.post_message(WallpaperSelected(event.item.wallpaper))

    def get_current_wallpaper(self) -> dict[str, Any] | None:
        """Get the currently highlighted wallpaper."""
        lv = self.query_one("#wallpaper-list", ListView)
        if lv.highlighted_child and isinstance(lv.highlighted_child, WallpaperListItem):
            return lv.highlighted_child.wallpaper
        return None

    @property
    def count(self) -> int:
        return len(self._wallpapers)

    def focus_list(self) -> None:
        """Focus the list view."""
        lv = self.query_one("#wallpaper-list", ListView)
        lv.focus()
