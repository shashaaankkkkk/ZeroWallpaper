"""Widget for managing multiple wallpaper playlists within the main app view."""

from __future__ import annotations

from typing import TYPE_CHECKING
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import ListView, ListItem, Static, Label

if TYPE_CHECKING:
    from zerowallpaper.tui.app import ZeroWallpaperApp


class PlaylistListItem(ListItem):
    """An item representing a playlist in the sidebar."""

    def __init__(self, name: str, is_active: bool = False) -> None:
        super().__init__()
        self.playlist_name = name
        self.is_active = is_active

    def compose(self) -> ComposeResult:
        active_mark = " ★" if self.is_active else ""
        yield Label(f" {self.playlist_name}{active_mark}")


class PlaylistManagerView(Widget):
    """A widget for managing multiple playlists, intended for use in a ContentSwitcher."""

    BINDINGS = [
        ("n", "new_playlist", "New Playlist"),
        ("d", "delete_playlist", "Delete Playlist"),
        ("s", "set_active", "Set Active"),
        ("r", "remove_wallpaper", "Remove Wallpaper"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app: ZeroWallpaperApp

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="mgr-sidebar", classes="sidebar"):
                yield Static(" ♬ PLAYLISTS", classes="sidebar-title")
                yield ListView(id="mgr-playlist-list")
                yield Static("\n [dim]n:new  d:delete  s:set active[/dim]", classes="sidebar-help")
            
            with Vertical(id="mgr-content"):
                yield Static(" ◆ WALLPAPERS IN PLAYLIST", classes="panel-title", id="mgr-playlist-title")
                yield ListView(id="mgr-wp-list")
                yield Static("\n [dim]r:remove selected wallpaper[/dim]", id="mgr-content-help")

    def action_new_playlist(self) -> None:
        """Create a new playlist."""
        from zerowallpaper.tui.screens import InputScreen
        
        def on_submit(name: str | None) -> None:
            if name and name.strip():
                self.app._playlist.create_playlist(name.strip())
                self.refresh_playlists()
                self.app.notify(f"Created playlist: {name}", title="♬ New")

        self.app.push_screen(InputScreen("Create New Playlist", "Playlist Name"), on_submit)

    def action_delete_playlist(self) -> None:
        """Delete the highlighted playlist."""
        lv = self.query_one("#mgr-playlist-list", ListView)
        if lv.highlighted_child:
            name = lv.highlighted_child.playlist_name
            if name == "Default":
                self.app.notify("Cannot delete Default playlist", severity="error")
                return
            
            self.app._playlist.delete_playlist(name)
            self.refresh_playlists()
            self.app.notify(f"Deleted playlist: {name}", title="♬ Deleted")

    def action_set_active(self) -> None:
        """Set the highlighted playlist as active."""
        lv = self.query_one("#mgr-playlist-list", ListView)
        if lv.highlighted_child:
            name = lv.highlighted_child.playlist_name
            self.app._playlist.set_active(name)
            self.refresh_playlists()
            self.app.notify(f"Active playlist: {name}", title="♬ Set Active")

    def action_remove_wallpaper(self) -> None:
        """Remove selected wallpaper from current playlist."""
        sidebar_lv = self.query_one("#mgr-playlist-list", ListView)
        wp_lv = self.query_one("#mgr-wp-list", ListView)
        
        if sidebar_lv.highlighted_child and wp_lv.highlighted_child:
            playlist_name = sidebar_lv.highlighted_child.playlist_name
            # The label is " ▸ filename"
            label = wp_lv.highlighted_child.query_one(Label).plain
            filename = label.replace(" ▸ ", "").strip()
            
            self.app._playlist.remove(filename, playlist_name)
            self.refresh_wallpapers()
            self.app.notify(f"Removed: {filename}", title="♬ Removed")

    def on_mount(self) -> None:
        self.refresh_playlists()

    def refresh_playlists(self) -> None:
        """Refresh the list of playlists."""
        lv = self.query_one("#mgr-playlist-list", ListView)
        lv.clear()
        
        active_name = self.app._playlist.active_name
        for name in self.app._playlist.playlist_names:
            lv.append(PlaylistListItem(name, is_active=(name == active_name)))
        
        if lv.children:
            lv.index = 0
            self.refresh_wallpapers()

    def refresh_wallpapers(self) -> None:
        """Refresh the list of wallpapers in the selected playlist."""
        sidebar_lv = self.query_one("#mgr-playlist-list", ListView)
        if not sidebar_lv.highlighted_child:
            return
            
        selected_name = sidebar_lv.highlighted_child.playlist_name
        self.query_one("#mgr-playlist-title", Static).update(f" ◆ WALLPAPERS IN: [b]{selected_name}[/b]")
        
        wp_list = self.query_one("#mgr-wp-list", ListView)
        wp_list.clear()
        
        filenames = self.app._playlist.get_all(selected_name)
        for fn in filenames:
            wp_list.append(ListItem(Label(f" ▸ {fn}")))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id == "mgr-playlist-list":
            self.refresh_wallpapers()
