import sys, select, termios, tty
def probe():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        sys.stdout.write("\033[c")
        sys.stdout.flush()
        response = ""
        while True:
            r, _, _ = select.select([sys.stdin], [], [], 0.1)
            if not r: break
            char = sys.stdin.read(1)
            response += char
            if char == "c": break
        return response
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

print(repr(probe()))
