import sys, os
with open(os.devnull, 'w') as devnull:
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = devnull
    sys.stderr = devnull
    try:
        from textual_image.widget import Image as TextualImage
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

from textual.app import App
class TestApp(App):
    def compose(self):
        yield TextualImage(sys.argv[1])
if __name__ == "__main__":
    TestApp().run()
