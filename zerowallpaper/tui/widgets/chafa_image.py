"""High-fidelity Unicode block rendering using the Chafa engine."""

import io
from pathlib import Path

from rich.text import Text

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    from chafa import Canvas, CanvasConfig, PixelMode, PixelType
    HAS_CHAFA = True
except ImportError:
    HAS_CHAFA = False


def generate_chafa_image(
    image_data_or_path: bytes | Path | str, width: int, height: int
) -> Text | None:
    """Generate an ultra-high-definition Unicode block image using Chafa.
    
    Returns a Rich Text renderable containing the ANSI escape sequences,
    or None if Chafa/Pillow are not available or decoding fails.
    """
    if not HAS_PILLOW or not HAS_CHAFA:
        return None

    try:
        if isinstance(image_data_or_path, bytes):
            img = Image.open(io.BytesIO(image_data_or_path))
        else:
            img = Image.open(image_data_or_path)

        if img.mode != "RGB":
            img = img.convert("RGB")

        config = CanvasConfig()
        # Chafa automatically handles aspect ratio fitting. We provide the 
        # maximum available terminal cells.
        config.width = width
        config.height = height
        # Use symbols mode which intelligently mixes half-blocks, braille, 
        # and true-color backgrounds for maximum fidelity.
        config.pixel_mode = PixelMode.CHAFA_PIXEL_MODE_SYMBOLS

        canvas = Canvas(config)
        
        # Feed the raw RGB bytes to the Chafa rendering engine
        canvas.draw_all_pixels(
            PixelType.CHAFA_PIXEL_RGB8,
            img.tobytes(),
            img.width,
            img.height,
            img.width * 3,
        )
        
        ansi_str = canvas.print().decode("utf-8")
        
        # Convert the raw ANSI string into a Rich Text renderable which Textual 
        # can display natively without breaking layout!
        return Text.from_ansi(ansi_str)

    except Exception:
        return None
