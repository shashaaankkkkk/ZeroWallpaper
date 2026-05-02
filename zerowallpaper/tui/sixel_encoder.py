import io
from pathlib import Path
from functools import lru_cache

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    from textual_image._sixel import image_to_sixels
    HAS_SIXEL_ENCODER = True
except ImportError:
    HAS_SIXEL_ENCODER = False

# Approximate standard terminal cell pixel dimensions
CELL_W = 10
CELL_H = 20

@lru_cache(maxsize=16)
def encode_sixel_cached(file_path_or_bytes, avail_chars_w: int, avail_chars_h: int) -> str:
    """Generate a Sixel escape sequence for an image, maintaining aspect ratio."""
    if not HAS_PILLOW or not HAS_SIXEL_ENCODER:
        return ""

    if isinstance(file_path_or_bytes, bytes):
        img = Image.open(io.BytesIO(file_path_or_bytes))
    else:
        img = Image.open(file_path_or_bytes)
        
    # Convert to RGB to ensure compatibility
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
        
    # Calculate target pixel dimensions
    target_w_px = avail_chars_w * CELL_W
    target_h_px = avail_chars_h * CELL_H
    
    img_aspect = img.width / max(1, img.height)
    avail_aspect = target_w_px / max(1, target_h_px)
    
    if img_aspect > avail_aspect:
        # Fit to width
        final_w = target_w_px
        final_h = int(final_w / img_aspect)
    else:
        # Fit to height
        final_h = target_h_px
        final_w = int(final_h * img_aspect)
        
    final_w = max(1, final_w)
    final_h = max(1, final_h)
    
    img = img.resize((final_w, final_h), Image.Resampling.LANCZOS)
    
    # textual_image._sixel.image_to_sixels generates the string
    return image_to_sixels(img)
