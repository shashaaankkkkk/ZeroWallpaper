"""Search engine for filtering wallpapers by tags, name, and category."""

from __future__ import annotations

from typing import Any


class SearchEngine:
    """Search and filter wallpapers from the index."""

    def __init__(self) -> None:
        self._wallpapers: list[dict[str, Any]] = []
        self._tags: dict[str, int] = {}

    def load_index(self, index: dict[str, Any]) -> None:
        """Load wallpaper data from index."""
        self._wallpapers = index.get("wallpapers", [])
        self._tags = index.get("tags", {})

    @property
    def total_count(self) -> int:
        return len(self._wallpapers)

    @property
    def all_tags(self) -> dict[str, int]:
        return dict(self._tags)

    @property
    def all_wallpapers(self) -> list[dict[str, Any]]:
        return list(self._wallpapers)

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search wallpapers by query string matching tags and filename."""
        if not query.strip():
            return list(self._wallpapers)

        tokens = [t.strip().lower() for t in query.split() if t.strip()]
        results = []

        for wp in self._wallpapers:
            fn_lower = wp["filename"].lower()
            wp_tags = [t.lower() for t in wp.get("tags", [])]
            cat = wp.get("category", "").lower()

            # All tokens must match something
            if all(
                any(tok in tag for tag in wp_tags)
                or tok in fn_lower
                or tok in cat
                for tok in tokens
            ):
                results.append(wp)

        return results

    def filter_by_tags(
        self, tags: list[str], mode: str = "or"
    ) -> list[dict[str, Any]]:
        """Filter wallpapers by tags.

        Args:
            tags: List of tag strings to filter by.
            mode: 'and' requires all tags, 'or' requires any tag.
        """
        if not tags:
            return list(self._wallpapers)

        tags_lower = {t.lower() for t in tags}
        results = []

        for wp in self._wallpapers:
            wp_tags = {t.lower() for t in wp.get("tags", [])}
            if mode == "and":
                if tags_lower.issubset(wp_tags):
                    results.append(wp)
            else:
                if tags_lower & wp_tags:
                    results.append(wp)

        return results

    def filter_by_category(self, category: str) -> list[dict[str, Any]]:
        """Filter wallpapers by category."""
        cat_lower = category.lower()
        return [
            wp for wp in self._wallpapers
            if wp.get("category", "").lower() == cat_lower
        ]

    def combined_filter(
        self,
        query: str = "",
        tags: list[str] | None = None,
        category: str = "",
    ) -> list[dict[str, Any]]:
        """Apply combined filters: query + tags + category."""
        results = list(self._wallpapers)

        if query.strip():
            query_set = set(w["filename"] for w in self.search(query))
            results = [w for w in results if w["filename"] in query_set]

        if tags:
            tag_set = set(w["filename"] for w in self.filter_by_tags(tags))
            results = [w for w in results if w["filename"] in tag_set]

        if category:
            results = [
                w for w in results
                if w.get("category", "").lower() == category.lower()
            ]

        return results
