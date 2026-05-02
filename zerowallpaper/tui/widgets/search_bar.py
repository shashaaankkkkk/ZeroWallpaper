"""Search bar widget with real-time filtering."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Input


class SearchChanged(Message):
    """Posted when search query changes."""

    def __init__(self, query: str) -> None:
        super().__init__()
        self.query = query


class SearchBar(Widget):
    """Search bar with icon and result count."""

    result_count = reactive(0)
    total_count = reactive(0)

    def compose(self) -> ComposeResult:
        with Horizontal(id="search-container"):
            yield Static(" 🔍", id="search-icon")
            yield Input(
                placeholder="Search wallpapers... (tags, names)",
                id="search-input",
            )
            yield Static("", id="result-count")

    def on_mount(self) -> None:
        self._update_count_display()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.post_message(SearchChanged(event.value))

    def watch_result_count(self, value: int) -> None:
        self._update_count_display()

    def watch_total_count(self, value: int) -> None:
        self._update_count_display()

    def _update_count_display(self) -> None:
        try:
            label = self.query_one("#result-count", Static)
            if self.result_count == self.total_count:
                label.update(f" {self.total_count} items ")
            else:
                label.update(f" {self.result_count}/{self.total_count} ")
        except Exception:
            pass

    def set_counts(self, result: int, total: int) -> None:
        self.result_count = result
        self.total_count = total

    def focus_input(self) -> None:
        inp = self.query_one("#search-input", Input)
        inp.focus()

    def clear(self) -> None:
        inp = self.query_one("#search-input", Input)
        inp.value = ""
