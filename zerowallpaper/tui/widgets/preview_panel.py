"""Preview panel widget for displaying wallpaper images in terminal."""

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from typing import Any

from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment
from rich.style import Style
from rich.text import Text

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static, Label

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class HalfBlockImage:
    """Rich renderable that converts an image to half-block Unicode characters.

    Uses the ▀ (upper half block) character with fg/bg colors to render
    two vertical pixels per character cell.
    """

    def __init__(
        self,
        image_data: bytes | None = None,
        image_path: Path | None = None,
        width: int = 30,
        height: int = 20,
    ) -> None:
        self.width = width
        self.height = height
        self._pixels: list[list[tuple[int, int, int]]] = []

        if HAS_PILLOW and (image_data or image_path):
            self._load_image(image_data, image_path)

    def _load_image(
        self,
        image_data: bytes | None,
        image_path: Path | None,
    ) -> None:
        """Load and resize image to target dimensions."""
        try:
            if image_data:
                img = Image.open(BytesIO(image_data))
            elif image_path:
                img = Image.open(image_path)
            else:
                return

            img = img.convert("RGB")

            # Height in pixels is 2x character height (2 pixels per char row)
            pixel_h = self.height * 2
            pixel_w = self.width

            # With half-block rendering (▀), each char cell displays 2 vertical
            # pixels. Since char cells are ~2x tall as wide, and we pack 2 pixels
            # vertically, the effective pixel aspect is 1:1 — no correction needed.
            img_aspect = img.width / img.height

            if (pixel_w / pixel_h) > img_aspect:
                # Available area is wider than image — fit to height
                pixel_w = int(pixel_h * img_aspect)
            else:
                # Available area is taller than image — fit to width
                pixel_h = int(pixel_w / img_aspect)

            pixel_h = max(2, pixel_h - (pixel_h % 2))  # Ensure even
            pixel_w = max(1, pixel_w)

            img = img.resize((pixel_w, pixel_h), Image.LANCZOS)
            self.width = pixel_w
            self.height = pixel_h // 2

            self._pixels = []
            for y in range(pixel_h):
                row = []
                for x in range(pixel_w):
                    row.append(img.getpixel((x, y)))
                self._pixels.append(row)

        except Exception:
            self._pixels = []

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        if not self._pixels:
            yield Text("  No preview available", style="dim")
            return

        h = len(self._pixels)
        w = len(self._pixels[0]) if h > 0 else 0

        for y in range(0, h - 1, 2):
            segments = []
            for x in range(w):
                top = self._pixels[y][x]
                bot = self._pixels[y + 1][x] if y + 1 < h else (0, 0, 0)

                fg = f"rgb({top[0]},{top[1]},{top[2]})"
                bg = f"rgb({bot[0]},{bot[1]},{bot[2]})"

                segments.append(
                    Segment("▀", Style(color=fg, bgcolor=bg))
                )
            segments.append(Segment("\n"))
            yield from segments


class PreviewPanel(Widget):
    """Right panel showing wallpaper preview and metadata."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_wp: dict[str, Any] | None = None
        self._loading = False

    def compose(self) -> ComposeResult:
        yield Static(" ◉ PREVIEW", classes="panel-title")
        yield Vertical(id="preview-image-container")
        yield Vertical(id="preview-meta")

    def on_mount(self) -> None:
        """Set initial placeholder after mount."""
        container = self.query_one("#preview-image-container", Vertical)
        container.mount(Static(
            "  Select a wallpaper\n  to preview",
            id="pv-placeholder",
        ))

    def _clear_container(self) -> None:
        """Remove all children from the preview container."""
        container = self.query_one("#preview-image-container", Vertical)
        container.remove_children()

    def _clear_meta(self) -> None:
        """Remove all children from the metadata section."""
        meta = self.query_one("#preview-meta", Vertical)
        meta.remove_children()

    def show_placeholder(self, text: str = "Select a wallpaper\nto preview") -> None:
        """Show placeholder text in preview area."""
        self._clear_container()
        self._clear_meta()
        container = self.query_one("#preview-image-container", Vertical)
        container.mount(Static(f"  {text}"))

    def show_loading(self) -> None:
        """Show loading state."""
        self._clear_container()
        container = self.query_one("#preview-image-container", Vertical)
        container.mount(Static("  ◌ Loading preview..."))

    def show_preview(
        self,
        image_data: bytes,
        wallpaper: dict[str, Any],
    ) -> None:
        """Render image preview and metadata."""
        self._current_wp = wallpaper
        self._clear_container()
        container = self.query_one("#preview-image-container", Vertical)

        # Calculate available size
        avail_w = max(10, container.size.width - 2)
        avail_h = max(5, container.size.height - 2)

        if HAS_PILLOW:
            img_renderable = HalfBlockImage(
                image_data=image_data,
                width=avail_w,
                height=avail_h,
            )
            container.mount(Static(img_renderable))
        else:
            container.mount(Static("  Pillow required\n  for previews"))

        # Update metadata
        self._update_metadata(wallpaper)

    def show_cached_preview(
        self,
        image_path: Path,
        wallpaper: dict[str, Any],
    ) -> None:
        """Render preview from cached file."""
        self._current_wp = wallpaper
        self._clear_container()
        container = self.query_one("#preview-image-container", Vertical)

        avail_w = max(10, container.size.width - 2)
        avail_h = max(5, container.size.height - 2)

        if HAS_PILLOW:
            img_renderable = HalfBlockImage(
                image_path=image_path,
                width=avail_w,
                height=avail_h,
            )
            container.mount(Static(img_renderable))
        else:
            container.mount(Static("  Pillow required"))

        self._update_metadata(wallpaper)

    def _update_metadata(self, wp: dict[str, Any]) -> None:
        """Update the metadata section below the preview."""
        self._clear_meta()
        meta = self.query_one("#preview-meta", Vertical)

        # Filename
        fn = wp.get("filename", "unknown")
        meta.mount(Static(f"  [b]{fn}[/b]"))

        # Tags
        tags = wp.get("tags", [])
        if tags:
            tag_str = " ".join(f"[{t}]" for t in tags[:6])
            meta.mount(Static(f"  {tag_str}", classes="meta-tags"))

        # Size
        size = wp.get("size_bytes", 0)
        if size > 0:
            from zerowallpaper.tui.widgets.wallpaper_list import format_size
            meta.mount(Static(f"  Size: {format_size(size)}"))

        # Category
        cat = wp.get("category", "")
        if cat:
            meta.mount(Static(f"  Category: {cat.title()}"))
