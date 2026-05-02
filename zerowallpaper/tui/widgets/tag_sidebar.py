"""Tag sidebar widget for filtering wallpapers."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Label, ListView, ListItem


class TagFilterChanged(Message):
    """Posted when tag filter selection changes."""

    def __init__(self, active_tags: list[str], special_filter: str = "") -> None:
        super().__init__()
        self.active_tags = active_tags
        self.special_filter = special_filter  # "all", "favorites", "recent"


class TagItem(ListItem):
    """A single tag item in the sidebar."""

    selected = reactive(False)

    def __init__(self, tag_name: str, count: int = 0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.tag_name = tag_name
        self.tag_count = count
        self.add_class("tag-item")

    def compose(self) -> ComposeResult:
        yield Label(self._get_label_text())

    def _get_label_text(self) -> str:
        marker = "●" if self.selected else "○"
        count_str = f" ({self.tag_count})" if self.tag_count > 0 else ""
        return f" {marker} {self.tag_name}{count_str}"

    def watch_selected(self, value: bool) -> None:
        try:
            self.query_one(Label).update(self._get_label_text())
        except Exception:
            pass
        if value:
            self.add_class("--selected")
        else:
            self.remove_class("--selected")


class SpecialFilterItem(ListItem):
    """Special filter items like All, Favorites, Recent."""

    selected = reactive(False)

    def __init__(self, label: str, icon: str, filter_key: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.filter_label = label
        self.icon = icon
        self.filter_key = filter_key
        self.add_class("tag-item")

    def compose(self) -> ComposeResult:
        yield Label(self._get_label_text())

    def _get_label_text(self) -> str:
        marker = "▸" if self.selected else " "
        return f" {marker} {self.icon} {self.filter_label}"

    def watch_selected(self, value: bool) -> None:
        try:
            self.query_one(Label).update(self._get_label_text())
        except Exception:
            pass
        if value:
            self.add_class("--selected")
        else:
            self.remove_class("--selected")


class TagSidebar(Widget):
    """Sidebar with tag filters and special categories."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tag_items: list[TagItem] = []

    def compose(self) -> ComposeResult:
        yield Static(" ⬡ FILTERS", classes="sidebar-title")
        with ListView(id="tag-list"):
            # Special filters
            yield SpecialFilterItem("All", "◈", "all", id="filter-all")
            yield SpecialFilterItem("Favorites", "★", "favorites", id="filter-fav")
            yield SpecialFilterItem("Cached", "💾", "cached", id="filter-cached")
            yield SpecialFilterItem("Recent", "◷", "recent", id="filter-recent")

            # Header is just a disabled list item
            yield ListItem(Static(" ─── TAGS ───", classes="tag-section-header"), disabled=True)

    def on_mount(self) -> None:
        # Select "All" by default
        all_filter = self.query_one("#filter-all", SpecialFilterItem)
        all_filter.selected = True

    def set_tags(self, tags: dict[str, int]) -> None:
        """Populate tags in the sidebar."""
        tag_list = self.query_one("#tag-list", ListView)
        
        # Remove existing tags (but keep special filters and header)
        for item in tag_list.query(TagItem):
            item.remove()

        self._tag_items = []
        for tag_name, count in tags.items():
            item = TagItem(tag_name, count)
            self._tag_items.append(item)
            tag_list.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle keyboard or mouse selection of sidebar items."""
        item = event.item
        if isinstance(item, SpecialFilterItem):
            # Clear tags
            self.clear_tag_selection()
            # Clear other special filters
            self.clear_special_selection()
            item.selected = True

            self.post_message(TagFilterChanged(
                active_tags=[],
                special_filter=item.filter_key,
            ))
        elif isinstance(item, TagItem):
            # Toggle this tag
            item.selected = not item.selected
            
            # Clear special filters visually
            self.clear_special_selection()

            self.post_message(TagFilterChanged(
                active_tags=self.get_active_tags(),
                special_filter="",
            ))

    def get_active_tags(self) -> list[str]:
        """Get list of currently selected tags."""
        return [
            item.tag_name
            for item in self._tag_items
            if item.selected
        ]

    def clear_tag_selection(self) -> None:
        """Clear all tag selections."""
        for item in self._tag_items:
            item.selected = False

    def clear_special_selection(self) -> None:
        """Clear special filter selections."""
        for child in self.query(SpecialFilterItem):
            child.selected = False
