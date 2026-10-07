"""0W07 — entry point."""
import os
import sys
import tkinter as tk
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def _excepthook(exc, val, tb):
    print("\n!!! Uncaught exception !!!", file=sys.stderr)
    traceback.print_exception(exc, val, tb, file=sys.stderr)


sys.excepthook = _excepthook

from core.sounds import SOUNDS
from core.retro_window import RetroWindow
from desktop.desktop import OW07Desktop

try:
    import doom
    HAS_DOOM = True
except Exception as e:
    print("doom.py not available:", e)
    HAS_DOOM = False


def main():
    if HAS_DOOM:
        try:
            doom.install_context(SOUNDS, RetroWindow)
        except Exception as e:
            print("doom context install failed:", e)

    app = OW07Desktop()
    app.root.mainloop()


if __name__ == "__main__":
    main()