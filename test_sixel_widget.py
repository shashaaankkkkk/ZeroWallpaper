import os
os.environ["ZEROWALLPAPER_SIXEL"] = "1"

from textual.app import App
from zerowallpaper.tui.sixel_encoder import encode_sixel_cached
from zerowallpaper.tui.widgets.sixel_image import SixelImage

class TestApp(App):
    def compose(self):
        payload = encode_sixel_cached('/Users/shashank/.zerowallpaper/cache/wallpapers/abstract.jpg', 40, 20)
        yield SixelImage(payload, width=40, height=20)
        
    def on_mount(self):
        self.exit()

if __name__ == "__main__":
    TestApp().run()
