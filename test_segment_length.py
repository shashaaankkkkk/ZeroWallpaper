from textual.app import App
from textual.strip import Strip
from textual.widget import Widget
from rich.segment import Segment

class SpoofWidget(Widget):
    def render_line(self, y: int) -> Strip:
        # A Segment with control=False, but text length = 0?
        # Rich computes cell_length automatically. We can override it?
        # Segment is a NamedTuple in older Rich, but a class in newer.
        # Let's see if we can subclass Segment or create a custom Renderable.
        pass

import rich.segment
print(type(rich.segment.Segment("a")))
