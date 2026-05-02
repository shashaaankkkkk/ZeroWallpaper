import sys, builtins
original_open = builtins.open
def mock_open(*args, **kwargs):
    if args and args[0] == "/dev/tty":
        raise OSError("TTY probing disabled")
    return original_open(*args, **kwargs)

builtins.open = mock_open
try:
    import textual_image.widget
    print("Import succeeded without /dev/tty!")
except Exception as e:
    print(f"Import failed: {e}")
finally:
    builtins.open = original_open
