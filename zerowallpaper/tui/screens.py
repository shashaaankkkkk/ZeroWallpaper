"""Screens for the ZeroWallpaper TUI."""

from __future__ import annotations

import webbrowser
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Static, Footer, OptionList, Input
from textual.widgets.option_list import Option

from zerowallpaper.tui.widgets.tag_sidebar import TagFilterChanged


class InputScreen(ModalScreen[str | None]):
    """A simple modal with an input field."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, title: str, placeholder: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.title_text = title
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical(id="input-screen-container"):
            yield Static(self.title_text, id="input-screen-title")
            yield Input(placeholder=self.placeholder, id="input-field")
            with Horizontal(id="input-screen-actions"):
                yield Button("OK", id="btn-ok", variant="primary")
                yield Button("Cancel", id="btn-cancel")

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ok":
            val = self.query_one("#input-field", Input).value
            self.dismiss(val)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)


class PlaylistSelectionScreen(ModalScreen[str | None]):
    """A modal to pick a playlist to add a wallpaper to."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, playlists: list[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self.playlists = playlists

    def compose(self) -> ComposeResult:
        with Vertical(id="playlist-select-container"):
            yield Static("Add to Playlist", id="playlist-select-title")
            yield OptionList(
                *[Option(p, id=p) for p in self.playlists],
                Option("+ Create New Playlist", id="--create-new--"),
                id="playlist-options"
            )
            with Horizontal(id="playlist-select-actions"):
                yield Button("Cancel", id="btn-cancel")

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Return the selected playlist name."""
        self.dismiss(event.option.id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)


class HomeScreen(Screen[None]):
    """The Home Screen overlay shown on startup."""

    BINDINGS = [
        Binding("e", "explore", "Explore Wallpapers"),
        Binding("m", "playlist_mgr", "Playlist Manager"),
        Binding("c", "cached", "Cached Wallpapers"),
        Binding("f", "favorites", "Favorites"),
        Binding("escape", "explore", "Explore", show=False),
        Binding("down", "focus_next", "Next", show=False),
        Binding("up", "focus_previous", "Previous", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="home-container"):
            # Title Section
            yield Static(
                "  _____               __          __   _ _                             \n"
                " |__  /___ _ __ ___  \\ \\      / /_ _| | |_ __   __ _ _ __   ___ _ __ \n"
                "   / // _ \\ '__/ _ \\  \\ \\ /\\ / / _` | | | '_ \\ / _` | '_ \\ / _ \\ '__|\n"
                "  / /|  __/ | | (_) |  \\ V  V / (_| | | | |_) | (_| | |_) |  __/ |   \n"
                " /____\\___|_|  \\___/    \\_/\\_/ \\__,_|_|_| .__/ \\__,_| .__/ \\___|_|   \n"
                "                                        |_|         |_|              ",
                id="home-ascii"
            )
            yield Static(
                "[i]Made with love by @shashaaankkkkk[/i]",
                classes="home-subtitle"
            )
            yield Static(
                "GitHub: https://github.com/shashaaankkkkk/zerowallpaper",
                classes="home-link",
                id="home-link"
            )

            # Navigation Buttons
            with Vertical(id="home-buttons"):
                yield Button("Explore Wallpapers  [ E ]", id="btn_explore", variant="primary")
                yield Button("Playlist Manager    [ M ]", id="btn_playlist_mgr", variant="default")
                yield Button("Cached Wallpapers   [ C ]", id="btn_cached", variant="default")
                yield Button("Favorites           [ F ]", id="btn_favorites", variant="default")
        
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle navigation button clicks."""
        button_id = event.button.id

        if button_id == "btn_explore":
            self.dismiss()
            self.app.action_nav_explore()
            
        elif button_id == "btn_playlist_mgr":
            self.dismiss()
            self.app.action_manage_playlists()

        elif button_id == "btn_cached":
            self.dismiss()
            self.app.action_nav_explore() # Use explore + filter
            self.app.post_message(TagFilterChanged(active_tags=[], special_filter="cached"))
            
        elif button_id == "btn_favorites":
            self.dismiss()
            self.app.action_nav_favorites()

    def action_focus_next(self) -> None:
        """Focus the next button."""
        self.focus_next()

    def action_focus_previous(self) -> None:
        """Focus the previous button."""
        self.focus_previous()

    def action_explore(self) -> None:
        """Dismiss modal to explore."""
        self.dismiss()

    def action_playlist_mgr(self) -> None:
        """Route to playlist manager."""
        self.dismiss()
        self.app.action_manage_playlists()

    def action_cached(self) -> None:
        """Route to cached."""
        self.app.post_message(TagFilterChanged(active_tags=[], special_filter="cached"))
        self.dismiss()

    def action_favorites(self) -> None:
        """Route to favorites."""
        self.app.post_message(TagFilterChanged(active_tags=[], special_filter="favorites"))
        self.dismiss()

    def on_click(self, event: events.Click) -> None:
        """Handle clicking on the link."""
        if getattr(event.widget, "id", None) == "home-link":
            webbrowser.open("https://github.com/shashaaankkkkk/zerowallpaper")
