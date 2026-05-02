import os
import sys

# Completely disable term_image terminal queries to prevent garbage printing!
os.environ["TERM_IMAGE_QUERIES"] = "0"

import textual_image._terminal
# Patch the textual_image probe function
textual_image._terminal.get_cell_size = lambda: (10, 20)

try:
    from textual_image.widget import Image
    print("Successfully imported Image widget without ANY garbage!")
except Exception as e:
    print("Failed:", type(e).__name__, e)

