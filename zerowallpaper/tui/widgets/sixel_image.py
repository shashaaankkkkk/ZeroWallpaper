"""Widget for rendering native Sixel images in the terminal."""

from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.geometry import Size
from textual.strip import Strip
from textual.widget import Widget
from rich.segment import Segment
from rich.style import Style

from zerowallpaper.tui.sixel_detector import supports_sixel
from zerowallpaper.tui.sixel_encoder import encode_sixel_cached


class SixelImageRenderer(Widget):
    """A low-level widget that renders a raw Sixel escape sequence."""

    def __init__(self, sixel_payload: str, width: int, height: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._sixel_payload = sixel_payload
        self._img_width = width
        self._img_height = height
        self._style = Style()

    def get_content_width(self, container: Size, viewport: Size) -> int:
        return self._img_width

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        return self._img_height

    def render_line(self, y: int) -> Strip:
        if y >= self._img_height:
            return Strip.blank(self._img_width)
        if y < self._img_height - 1:
            return Strip([Segment(" " * self._img_width, self._style)])
        
        move_up = f"\033[{self._img_height - 1}A"
        move_down = f"\033[{self._img_height - 1}B"
        payload = move_up + self._sixel_payload + move_down
        
        return Strip([
            Segment(" " * self._img_width, self._style),
            Segment(payload, control=True)
        ])


class SixelImageWidget(Widget):
    """A high-level widget for simple image placement using Sixel."""

    def __init__(self, id: str | None = None, **kwargs) -> None:
        super().__init__(id=id, **kwargs)
        self._image_source: str | Path | None = None

    def set_image(self, source: str | Path | None) -> None:
        """Set the image to display (path or string)."""
        self._image_source = source
        self.refresh()

    def compose(self) -> ComposeResult:
        yield Vertical(id="sixel-inner-container")

    def on_resize(self) -> None:
        self.refresh()

    def refresh(self, *args, **kwargs) -> None:
        if not self.is_mounted or not self._image_source:
            return super().refresh(*args, **kwargs)

        # Clear and rebuild
        container = self.query_one(Vertical)
        container.remove_children()

        if supports_sixel():
            w = max(4, self.size.width)
            h = max(2, self.size.height)
            payload = encode_sixel_cached(str(self._image_source), w, h)
            if payload:
                container.mount(SixelImageRenderer(payload, width=w, height=h))
        
        return super().refresh(*args, **kwargs)


from textual.containers import Vertical
