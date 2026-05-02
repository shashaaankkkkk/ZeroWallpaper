import os
os.environ["ZEROWALLPAPER_SIXEL"] = "1"

from textual.app import App
from textual.strip import Strip
from rich.segment import Segment
from textual.widget import Widget
from rich.style import Style

class SixelLastLine(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.height = 10
        self.width = 20

    def render_line(self, y: int) -> Strip:
        if y == self.height - 1:
            move_up = f"\033[{self.height - 1}A"
            move_down = f"\033[{self.height - 1}B"
            payload = move_up + "\033Pq#0;2;0;0;0#1;2;100;100;100#2;2;0;100;0#1~~~\033\\" + move_down
            return Strip([
                Segment(" " * self.width),
                Segment(payload, control=True)
            ])
        return Strip([Segment(" " * self.width)])

class TestApp(App):
    def compose(self):
        yield SixelLastLine()
        
    def on_mount(self):
        self.exit()

if __name__ == "__main__":
    TestApp().run()
