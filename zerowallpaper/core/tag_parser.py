"""Tag parser for extracting tags from markdown page files."""

from __future__ import annotations

import re
from pathlib import Path


# Pattern: tags: `tag1` `tag2` ... \n<img src="URL">
TAG_LINE_PATTERN = re.compile(
    r'tags:\s*((?:`[^`]*`\s*)*)\s*\n\s*<img\s+src="([^"]+)"',
    re.IGNORECASE,
)

# Pattern to extract individual tags from backtick-wrapped text
BACKTICK_TAG_PATTERN = re.compile(r'`([^`]+)`')

# Category mapping based on page filename
CATEGORY_MAP = {
    "Desktop.md": "desktop",
    "Unix.md": "unix",
    "Mobile.md": "mobile",
    "Live.md": "live",
    "UltraWide.md": "ultrawide",
}

# Common words to ignore when extracting tags from filenames
FILENAME_STOP_WORDS = {
    "the", "and", "for", "with", "from", "img", "image", "wallpaper",
    "wallhaven", "pixiv", "4k", "hd", "uhd",
}


def parse_tags_from_markdown(
    markdown: str, page_name: str
) -> list[dict[str, list[str] | str]]:
    """Parse wallpaper tags from a markdown page.

    Expected format in markdown:
        tags: `tag1` `tag2`
        <img src="https://raw.githubusercontent.com/.../images/filename.ext">

    Args:
        markdown: Raw markdown content.
        page_name: Name of the page file (e.g., 'Page1.md').

    Returns:
        List of dicts with 'filename', 'tags', and 'category'.
    """
    results = []
    category = _get_category(page_name)

    for match in TAG_LINE_PATTERN.finditer(markdown):
        tag_string = match.group(1)
        image_url = match.group(2)

        # Extract filename from URL
        filename = image_url.rsplit("/", 1)[-1] if "/" in image_url else image_url

        # Extract individual tags from backtick-wrapped text
        tags = BACKTICK_TAG_PATTERN.findall(tag_string)
        tags = [t.strip().lower() for t in tags if t.strip()]

        results.append({
            "filename": filename,
            "tags": tags,
            "category": category,
            "page": page_name.replace(".md", ""),
        })

    return results


def extract_tags_from_filename(filename: str) -> list[str]:
    """Extract tags from a filename as fallback when markdown tags are missing.

    Splits on hyphens, underscores, and dots. Filters out stop words
    and very short tokens.

    Args:
        filename: Image filename (e.g., 'anime-nord-dark.png').

    Returns:
        List of extracted tag strings.
    """
    stem = Path(filename).stem.lower()

    # Split on common separators
    tokens = re.split(r'[-_.\s]+', stem)

    tags = []
    for token in tokens:
        token = token.strip()
        # Skip empty, short, numeric-only, or stop words
        if (
            len(token) < 2
            or token.isdigit()
            or token in FILENAME_STOP_WORDS
        ):
            continue
        tags.append(token)

    return tags


def _get_category(page_name: str) -> str:
    """Determine wallpaper category from page filename."""
    if page_name in CATEGORY_MAP:
        return CATEGORY_MAP[page_name]

    # Page1.md through Page15.md are desktop wallpapers
    if page_name.startswith("Page"):
        return "desktop"

    return "other"


def build_tag_mapping(
    pages: dict[str, str],
    all_filenames: list[str],
) -> dict[str, dict]:
    """Build a complete tag mapping for all wallpapers.

    Parses markdown pages for tags, and falls back to filename-based
    extraction for wallpapers not found in any page.

    Args:
        pages: Dict mapping page name to markdown content.
        all_filenames: List of all image filenames from the repository.

    Returns:
        Dict mapping filename to {'tags': [...], 'category': '...', 'page': '...'}.
    """
    mapping: dict[str, dict] = {}

    # Parse tags from all markdown pages
    for page_name, content in pages.items():
        parsed = parse_tags_from_markdown(content, page_name)
        for entry in parsed:
            filename = entry["filename"]
            if filename not in mapping:
                mapping[filename] = {
                    "tags": entry["tags"],
                    "category": entry["category"],
                    "page": entry["page"],
                }
            else:
                # Merge tags from multiple pages
                existing_tags = set(mapping[filename]["tags"])
                existing_tags.update(entry["tags"])
                mapping[filename]["tags"] = sorted(existing_tags)

    # Fallback: extract tags from filenames for wallpapers not in markdown
    for filename in all_filenames:
        if filename not in mapping:
            tags = extract_tags_from_filename(filename)
            mapping[filename] = {
                "tags": tags,
                "category": "desktop",  # Default category
                "page": "",
            }

    return mapping


def get_all_unique_tags(tag_mapping: dict[str, dict]) -> dict[str, int]:
    """Get all unique tags with their occurrence count.

    Args:
        tag_mapping: The tag mapping from build_tag_mapping().

    Returns:
        Dict mapping tag name to count, sorted by count descending.
    """
    tag_counts: dict[str, int] = {}

    for entry in tag_mapping.values():
        for tag in entry.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Sort by count descending, then alphabetically
    return dict(
        sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))
    )
