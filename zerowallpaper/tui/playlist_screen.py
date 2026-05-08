"""Screen for managing multiple wallpaper playlists."""

from __future__ import annotations

from typing import TYPE_CHECKING
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Static, Label, Input

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


class PlaylistScreen(Screen):
    """A dedicated screen for managing multiple playlists."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("n", "new_playlist", "New Playlist"),
        Binding("d", "delete_playlist", "Delete"),
        Binding("s", "set_active", "Set Active"),
        Binding("r", "remove_wallpaper", "Remove WP"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app: ZeroWallpaperApp  # Type hint for the app

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="playlist-sidebar", classes="sidebar"):
                yield Static(" ⬡ PLAYLISTS", classes="sidebar-title")
                yield ListView(id="playlist-list")
                yield Static("\n [dim]n:new  d:delete  s:active[/dim]", classes="sidebar-help")
            
            with Vertical(id="playlist-content"):
                yield Static(" ◆ WALLPAPERS IN PLAYLIST", classes="panel-title", id="playlist-title")
                yield ListView(id="playlist-wp-list")
                yield Static("\n [dim]r:remove wallpaper from playlist[/dim]", id="content-help")
        
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_playlists()

    def _refresh_playlists(self) -> None:
        """Refresh the list of playlists."""
        lv = self.query_one("#playlist-list", ListView)
        lv.clear()
        
        active_name = self.app._playlist.active_name
        for name in self.app._playlist.playlist_names:
            lv.append(PlaylistListItem(name, is_active=(name == active_name)))
        
        if lv.children:
            lv.index = 0
            self._refresh_wallpapers()

    def _refresh_wallpapers(self) -> None:
        """Refresh the list of wallpapers in the selected playlist."""
        sidebar_lv = self.query_one("#playlist-list", ListView)
        if not sidebar_lv.highlighted_child:
            return
            
        selected_name = sidebar_lv.highlighted_child.playlist_name
        self.query_one("#playlist-title", Static).update(f" ◆ WALLPAPERS IN: [b]{selected_name}[/b]")
        
        wp_list = self.query_one("#playlist-wp-list", ListView)
        wp_list.clear()
        
        filenames = self.app._playlist.get_all(selected_name)
        for fn in filenames:
            wp_list.append(ListItem(Label(f" ▸ {fn}")))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id == "playlist-list":
            self._refresh_wallpapers()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_new_playlist(self) -> None:
        """Show input to create a new playlist."""
        def on_submit(name: str):
            if name and self.app._playlist.create_playlist(name):
                self._refresh_playlists()
                self.app.notify(f"Created playlist: {name}")
            self.app.pop_screen()

        self.app.push_screen(PlaylistInputDialog(on_submit))

    def action_delete_playlist(self) -> None:
        """Delete the selected playlist."""
        lv = self.query_one("#playlist-list", ListView)
        if lv.highlighted_child:
            name = lv.highlighted_child.playlist_name
            if name == "Default":
                self.app.notify("Cannot delete Default playlist", severity="warning")
                return
                
            if self.app._playlist.delete_playlist(name):
                self._refresh_playlists()
                self.app.notify(f"Deleted playlist: {name}")

    def action_set_active(self) -> None:
        """Set the selected playlist as active."""
        lv = self.query_one("#playlist-list", ListView)
        if lv.highlighted_child:
            name = lv.highlighted_child.playlist_name
            self.app._playlist.set_active(name)
            self._refresh_playlists()
            self.app.notify(f"Active playlist: {name}")

    def action_remove_wallpaper(self) -> None:
        """Remove selected wallpaper from current playlist."""
        sidebar_lv = self.query_one("#playlist-list", ListView)
        wp_lv = self.query_one("#playlist-wp-list", ListView)
        
        if sidebar_lv.highlighted_child and wp_lv.highlighted_child:
            playlist_name = sidebar_lv.highlighted_child.playlist_name
            # Extract filename from Label text " ▸ filename"
            label = wp_lv.highlighted_child.query_one(Label).renderable
            filename = str(label).replace(" ▸ ", "").strip()
            
            self.app._playlist.remove(filename, playlist_name)
            self._refresh_wallpapers()
            self.app.notify(f"Removed {filename}")


class PlaylistInputDialog(Screen):
    """Simple modal for entering a playlist name."""

    def __init__(self, callback) -> None:
        super().__init__()
        self.callback = callback

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Enter Playlist Name:"),
            Input(placeholder="e.g. Chill, Coding...", id="playlist-name-input"),
            id="dialog-container"
        )

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.callback(event.value)
