"""Index builder that combines GitHub API data with tag parsing."""

from __future__ import annotations

import time
from typing import Any

from zerowallpaper.core.cache import CacheManager
from zerowallpaper.core.github_api import GitHubFetcher
from zerowallpaper.core.tag_parser import build_tag_mapping, get_all_unique_tags


class IndexBuilder:
    """Builds and manages the wallpaper index."""

    def __init__(self, fetcher: GitHubFetcher, cache: CacheManager) -> None:
        self.fetcher = fetcher
        self.cache = cache

    async def build_index(self, force: bool = False) -> dict[str, Any]:
        """Build wallpaper index from GitHub API + markdown tags."""
        if not force:
            cached = self.cache.get_index()
            if cached:
                return cached

        images = await self.fetcher.fetch_image_tree()
        all_filenames = [img["filename"] for img in images]
        pages = await self.fetcher.fetch_all_pages()
        tag_mapping = build_tag_mapping(pages, all_filenames)

        wallpapers = []
        for img in images:
            fn = img["filename"]
            td = tag_mapping.get(fn, {})
            wallpapers.append({
                "filename": fn,
                "path": img["path"],
                "raw_url": img["raw_url"],
                "tags": td.get("tags", []),
                "category": td.get("category", "desktop"),
                "page": td.get("page", ""),
                "size_bytes": img.get("size_bytes", 0),
            })

        wallpapers.sort(key=lambda w: w["filename"].lower())
        tags = get_all_unique_tags(tag_mapping)
        categories = sorted(set(w["category"] for w in wallpapers))

        index = {
            "updated_at": time.time(),
            "wallpaper_count": len(wallpapers),
            "wallpapers": wallpapers,
            "tags": tags,
            "categories": categories,
        }
        self.cache.save_index(index)
        return index

    async def get_index(self) -> dict[str, Any]:
        """Get index, building if necessary."""
        return await self.build_index(force=False)

    async def refresh_index(self) -> dict[str, Any]:
        """Force refresh the index."""
        self.cache.force_invalidate_index()
        return await self.build_index(force=True)
