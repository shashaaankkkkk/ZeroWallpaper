import os
os.environ["TERM_IMAGE_QUERIES"] = "0"

from textual.app import App
from textual.widgets import Static
from term_image.image import KittyImage

KittyImage._forced_support = True

class TestApp(App):
    def compose(self):
        img = KittyImage.from_file('/Users/shashank/.zerowallpaper/cache/wallpapers/abstract.jpg')
        img.set_size(width=40)
        yield Static(str(img))
        
    def on_mount(self):
        self.exit()

if __name__ == "__main__":
    TestApp().run()
