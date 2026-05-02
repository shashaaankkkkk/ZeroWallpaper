from chafa import Canvas, CanvasConfig, PixelMode, PixelType
from PIL import Image

img = Image.open('/Users/shashank/.zerowallpaper/cache/wallpapers/abstract.jpg')
if img.mode != 'RGB':
    img = img.convert('RGB')

config = CanvasConfig()
config.width = 40
config.height = 20
config.pixel_mode = PixelMode.CHAFA_PIXEL_MODE_SYMBOLS

canvas = Canvas(config)
canvas.draw_all_pixels(PixelType.CHAFA_PIXEL_RGB8, img.tobytes(), img.width, img.height, img.width * 3)
output = canvas.print().decode('utf-8')
print("Output lines:", len(output.strip().split('\n')))
