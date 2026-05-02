"""Screens for the ZeroWallpaper TUI."""

from __future__ import annotations

import webbrowser
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Static, Footer

from zerowallpaper.tui.widgets.tag_sidebar import TagFilterChanged


class HomeScreen(Screen[None]):
    """The Home Screen overlay shown on startup."""

    BINDINGS = [
        Binding("e", "explore", "Explore Wallpapers"),
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
                yield Button("Cached Wallpapers   [ C ]", id="btn_cached", variant="default")
                yield Button("Favorites           [ F ]", id="btn_favorites", variant="default")
        
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle navigation button clicks."""
        button_id = event.button.id

        if button_id == "btn_explore":
            self.dismiss()
            
        elif button_id == "btn_cached":
            self.app.post_message(TagFilterChanged(active_tags=[], special_filter="cached"))
            self.dismiss()
            
        elif button_id == "btn_favorites":
            self.app.post_message(TagFilterChanged(active_tags=[], special_filter="favorites"))
            self.dismiss()

    def action_focus_next(self) -> None:
        """Focus the next button."""
        self.focus_next()

    def action_focus_previous(self) -> None:
        """Focus the previous button."""
        self.focus_previous()

    def action_explore(self) -> None:
        """Dismiss modal to explore."""
        self.dismiss()

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
