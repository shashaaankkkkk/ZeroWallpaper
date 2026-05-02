import sys
import textual_image._terminal

# Patch the buggy probe function
textual_image._terminal.get_cell_size = lambda: (10, 20)

try:
    from textual_image.widget import Image
    print("Successfully imported Image widget without hanging!")
except Exception as e:
    print("Failed:", type(e).__name__, e)

