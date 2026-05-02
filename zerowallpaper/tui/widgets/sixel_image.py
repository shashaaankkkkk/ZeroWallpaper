"""Widget for rendering native Sixel images in the terminal."""

from __future__ import annotations

from typing import cast
from textual.geometry import Size
from textual.strip import Strip
from textual.widget import Widget
from rich.segment import Segment
from rich.style import Style

class SixelImage(Widget):
    """A widget that renders a raw Sixel escape sequence inline.
    
    Because Textual strictly controls the screen layout, we must bypass 
    the standard text rendering by placing the entire Sixel payload into a
    single Segment with control=True on the first row of the widget.
    Remaining rows are padded with transparent spaces to reserve the geometry.
    """

    def __init__(self, sixel_payload: str, width: int, height: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._sixel_payload = sixel_payload
        self._img_width = width
        self._img_height = height
        
        # We need a style to keep Textual happy
        self._style = Style()

    def get_content_width(self, container: Size, viewport: Size) -> int:
        return self._img_width

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        return self._img_height

    def render_line(self, y: int) -> Strip:
        """Render a single line of the widget."""
        
        if y >= self._img_height:
            return Strip.blank(self._img_width)
            
        # For all rows before the last one, yield blank spaces
        if y < self._img_height - 1:
            return Strip([Segment(" " * self._img_width, self._style)])
            
        # On the VERY LAST row of the image, Textual has already drawn the blank
        # spaces for all the above rows. We now move the cursor UP to the start
        # of the image, dump the Sixel payload (which draws downwards over the
        # spaces), and then move the cursor DOWN back to the last line.
        # This prevents terminals like Kitty from erasing the Sixel graphic
        # when Textual draws the background spaces!
        
        move_up = f"\033[{self._img_height - 1}A"
        move_down = f"\033[{self._img_height - 1}B"
        payload = move_up + self._sixel_payload + move_down
        
        return Strip([
            Segment(" " * self._img_width, self._style),
            Segment(payload, control=True)
        ])
