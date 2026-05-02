"""Status bar widget showing app state and shortcuts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static


class StatusBar(Widget):
    """Bottom status bar showing mode, filters, cache, and shortcuts."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._mode = "Manual"
        self._filter_count = 0
        self._cache_count = 0
        self._network = "online"

    def compose(self) -> ComposeResult:
        with Horizontal(id="status-bar"):
            yield Static("", id="status-info")
            yield Static("", id="status-shortcuts", classes="status-shortcuts")

    def on_mount(self) -> None:
        self._update()

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self._update()

    def set_filter_count(self, count: int) -> None:
        self._filter_count = count
        self._update()

    def set_cache_count(self, count: int) -> None:
        self._cache_count = count
        self._update()

    def set_network(self, status: str) -> None:
        self._network = status
        self._update()

    def _update(self) -> None:
        try:
            info = self.query_one("#status-info", Static)
            mode_icon = "⚡" if self._mode != "Manual" else "◈"
            net_icon = "●" if self._network == "online" else "○"

            info.update(
                f" {mode_icon} {self._mode}"
                f"  │  ⏳ Filters: {self._filter_count}"
                f"  │  📦 Cache: {self._cache_count}"
                f"  │  {net_icon} {self._network.title()}"
            )

            shortcuts = self.query_one("#status-shortcuts", Static)
            shortcuts.update(
                "↑↓:nav  s:set  /:search  r:random  "
                "a:auto  f:fav  Tab:panel  q:quit "
            )
        except Exception:
            pass
