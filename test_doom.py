import traceback
import tkinter as tk
import doom


class FakeDesktop:
    windows = []
    def register_window(self, w, t):
        pass
    def unregister_window(self, w):
        pass
    def set_taskbar_state(self, w, minimized=False):
        pass
    def highlight_taskbar(self, w):
        pass


root = tk.Tk()
root.title("Doom test host")
root.geometry("1000x700")

try:
    print("calling DoomWindow...")
    w = doom.DoomWindow(root, desktop=FakeDesktop())
    print("DoomWindow returned:", w)
    print("has canvas?", hasattr(w, "canvas"))
    print("content children:", w.content.winfo_children() if hasattr(w, "content") else "NO CONTENT")
except Exception:
    traceback.print_exc()

root.mainloop()