"""Navigation Rail for the ZeroWallpaper Command Center."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Label


class NavRailItem(Widget):
    """A single item in the navigation rail."""
    
    can_focus = True

    def __init__(self, label: str, screen_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.rail_label = label
        self.screen_id = screen_id
        self.add_class("rail-item")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"{self.rail_label}", classes="rail-text")

    def on_click(self) -> None:
        self.app.post_message(self.RailItemSelected(self.screen_id))
        self.focus()

    class RailItemSelected(Message):
        def __init__(self, screen_id: str) -> None:
            super().__init__()
            self.screen_id = screen_id


class NavRail(Widget):
    """The left-side navigation rail."""

    def compose(self) -> ComposeResult:
        with Vertical(id="rail-container"):
            yield Static("ZERO", id="rail-logo")
            yield Static("───", classes="rail-divider")
            
            yield NavRailItem("BROWSE", "view-browser", id="rail-browse")
            yield NavRailItem("PLAYLIST", "view-manager", id="rail-playlist")
            
            yield Vertical(id="rail-spacer")
            yield Static("───", classes="rail-divider")
            yield Static(" v1.0 ", id="rail-version")

    def set_active(self, screen_id: str) -> None:
        """Mark the correct item as active."""
        for item in self.query(NavRailItem):
            if item.screen_id == screen_id:
                item.add_class("--active")
            else:
                item.remove_class("--active")
