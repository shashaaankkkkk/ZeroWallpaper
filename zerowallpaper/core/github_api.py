"""GitHub API client for fetching wallpaper data from D3Ext/aesthetic-wallpapers."""

from __future__ import annotations

import os
from typing import Any

import httpx


REPO_OWNER = "D3Ext"
REPO_NAME = "aesthetic-wallpapers"
REPO_BRANCH = "main"
API_BASE = "https://api.github.com"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{REPO_BRANCH}"

# Known page files in the repository
PAGE_FILES = [
    "Desktop.md", "Live.md", "Mobile.md", "UltraWide.md", "Unix.md",
    "Page1.md", "Page2.md", "Page3.md", "Page4.md", "Page5.md",
    "Page6.md", "Page7.md", "Page8.md", "Page9.md", "Page10.md",
    "Page11.md", "Page12.md", "Page13.md", "Page14.md", "Page15.md",
]

# Supported image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class GitHubAPIError(Exception):
    """Raised when GitHub API returns an error."""
    pass


class RateLimitError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded."""
    pass


class GitHubFetcher:
    """Async client for fetching data from the aesthetic-wallpapers GitHub repo."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self._client: httpx.AsyncClient | None = None

    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ZeroWallpaper/1.0",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self._get_headers(),
                timeout=httpx.Timeout(30.0, connect=10.0),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _api_get(self, url: str) -> Any:
        """Make a GET request to the GitHub API."""
        client = await self._get_client()
        response = await client.get(url)

        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "?")
            raise RateLimitError(
                f"GitHub API rate limit exceeded (remaining: {remaining}). "
                "Set GITHUB_TOKEN environment variable to increase limits."
            )

        if response.status_code != 200:
            raise GitHubAPIError(
                f"GitHub API error {response.status_code}: {response.text[:200]}"
            )

        return response.json()

    async def fetch_image_tree(self) -> list[dict[str, Any]]:
        """Fetch all image files from the repository using Git Trees API.

        Uses a single API call with recursive=1 to get all files
        in the images/ directory.

        Returns:
            List of dicts with 'path', 'size', 'sha' for each image file.
        """
        # First get the images directory tree SHA from root contents
        root_url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/contents/"
        root_contents = await self._api_get(root_url)

        images_sha = None
        for item in root_contents:
            if item["name"] == "images" and item["type"] == "dir":
                images_sha = item["sha"]
                break

        if not images_sha:
            raise GitHubAPIError("Could not find 'images' directory in repository")

        # Fetch the full tree recursively
        tree_url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{images_sha}?recursive=1"
        tree_data = await self._api_get(tree_url)

        images = []
        for item in tree_data.get("tree", []):
            if item["type"] != "blob":
                continue

            path = item["path"]
            # Filter to image files only
            ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
            if ext not in IMAGE_EXTENSIONS:
                continue

            images.append({
                "filename": path,
                "path": f"images/{path}",
                "raw_url": f"{RAW_BASE}/images/{path}",
                "size_bytes": item.get("size", 0),
                "sha": item["sha"],
            })

        return images

    async def fetch_page_markdown(self, page_name: str) -> str:
        """Fetch raw markdown content of a page file.

        Args:
            page_name: Name of the page file (e.g., 'Page1.md')

        Returns:
            Raw markdown content as string.
        """
        url = f"{RAW_BASE}/pages/{page_name}"
        client = await self._get_client()
        response = await client.get(url)

        if response.status_code != 200:
            raise GitHubAPIError(
                f"Failed to fetch page {page_name}: {response.status_code}"
            )

        return response.text

    async def fetch_all_pages(self) -> dict[str, str]:
        """Fetch all page markdown files.

        Returns:
            Dict mapping page name to markdown content.
        """
        pages: dict[str, str] = {}
        for page_name in PAGE_FILES:
            try:
                content = await self.fetch_page_markdown(page_name)
                pages[page_name] = content
            except GitHubAPIError:
                # Skip pages that fail to load
                continue
        return pages

    async def download_image(self, filename: str) -> bytes:
        """Download an image file from the repository.

        Args:
            filename: Image filename within the images/ directory.

        Returns:
            Raw image bytes.
        """
        url = f"{RAW_BASE}/images/{filename}"
        client = await self._get_client()
        response = await client.get(url)

        if response.status_code != 200:
            raise GitHubAPIError(
                f"Failed to download image {filename}: {response.status_code}"
            )

        return response.content

    async def check_rate_limit(self) -> dict[str, Any]:
        """Check current GitHub API rate limit status."""
        try:
            data = await self._api_get(f"{API_BASE}/rate_limit")
            core = data.get("resources", {}).get("core", {})
            return {
                "limit": core.get("limit", 60),
                "remaining": core.get("remaining", 0),
                "reset": core.get("reset", 0),
            }
        except GitHubAPIError:
            return {"limit": 60, "remaining": -1, "reset": 0}
    