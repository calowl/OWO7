# test_apps.py
import tkinter as tk
from apps.tetris import TetrisWindow
from apps.clock import ClockWindow
from apps.dice import DiceWindow
from apps.snake import SnakeWindow
from apps.pong import PongWindow
from apps.paint import PaintWindow
from apps.notepad import NotepadWindow
from apps.cmd import CommandPromptWindow
from apps.music_player import MusicPlayerWindow
from apps.file_explorer import FileExplorerWindow
from apps.calculator import CalculatorWindow
from apps.store import StoreWindow


class FakeDesktop:
    def register_window(self, w, t): pass
    def unregister_window(self, w): pass
    def set_taskbar_state(self, w, minimized=False): pass
    def highlight_taskbar(self, w): pass
    def refresh_desktop(self): pass
    def open_tetris(self): TetrisWindow(root, self)
    def open_clock(self): ClockWindow(root, self)
    def open_dice(self): DiceWindow(root, self)


root = tk.Tk()
root.title("0W07 apps test")
root.geometry("1400x900+0+0")

fd = FakeDesktop()

# Stagger the windows so they don't all pile up
apps = [TetrisWindow, ClockWindow, DiceWindow, SnakeWindow, PongWindow,
        PaintWindow, NotepadWindow, CommandPromptWindow,
        MusicPlayerWindow, FileExplorerWindow, CalculatorWindow,
        StoreWindow]

for i, cls in enumerate(apps):
    try:
        w = cls(root, fd)
        w.geometry(f"+{60 + i * 40}+{60 + i * 30}")
        print(f"opened {cls.__name__}")
    except Exception as e:
        print(f"{cls.__name__} FAILED: {e}")
        import traceback
        traceback.print_exc()

print("all done — entering mainloop")
root.mainloop()