from textual.app import App
from textual.widgets import Static
from rich.text import Text
from chafa import Canvas, CanvasConfig, PixelMode, PixelType
from PIL import Image

class TestApp(App):
    def compose(self):
        img = Image.open('/Users/shashank/.zerowallpaper/cache/wallpapers/abstract.jpg')
        img = img.resize((80, 40))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        config = CanvasConfig()
        config.width = 80
        config.height = 40
        config.pixel_mode = PixelMode.CHAFA_PIXEL_MODE_SYMBOLS
        
        canvas = Canvas(config)
        canvas.draw_all_pixels(PixelType.CHAFA_PIXEL_RGB8, img.tobytes(), img.width, img.height, img.width * 3)
        ansi_str = canvas.print().decode('utf-8')
        
        # We can yield a Static initialized with from_ansi!
        yield Static(Text.from_ansi(ansi_str))
        
    def on_mount(self):
        self.exit()

if __name__ == "__main__":
    TestApp().run()
