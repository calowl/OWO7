"""Retro window base class + font scaling helper."""
import tkinter as tk

from .state import TASKBAR_H


# ------------------------------------------------------------------
# Font rescaling
# ------------------------------------------------------------------
def rescale_fonts(widget, ratio):
    """Recursively scale every widget's font by `ratio`."""
    try:
        f = widget.cget("font")
        if isinstance(f, (tuple, list)) and len(f) >= 2 and isinstance(f[1], int):
            fam, size = f[0], f[1]
            new_size = max(6, int(round(size * ratio)))
            widget.config(font=(fam, new_size) + tuple(f[2:]))
    except Exception:
        pass
    for child in widget.winfo_children():
        rescale_fonts(child, ratio)


# ------------------------------------------------------------------
# RetroWindow
# ------------------------------------------------------------------
class RetroWindow(tk.Toplevel):
    def __init__(self, master, title="Window", width=300, height=200,
                 x=120, y=120, on_close=None, desktop=None, resizable=True):
        super().__init__(master)
        self.overrideredirect(True)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.configure(bg="#c0c0c0")

        self.on_close = on_close
        self.desktop = desktop
        self.minimized = False
        self.maximized = False
        self._prev_geo = None
        self.taskbar_btn = None

        # Title bar
        self.title_bar = tk.Frame(self, bg="#c85fa0", relief="raised", bd=2)
        self.title_bar.pack(fill="x")
        self.title_label = tk.Label(self.title_bar, text=title, bg="#c85fa0",
                                    fg="white", font=("MS Sans Serif", 8, "bold"))
        self.title_label.pack(side="left", padx=5)

        self.close_btn = tk.Button(self.title_bar, text="X", bg="#ffd6e8",
                                   fg="#7a2050", relief="raised", bd=1,
                                   command=self._close,
                                   activebackground="#ffb3d9",
                                   font=("MS Sans Serif", 8, "bold"), width=2)
        self.close_btn.pack(side="right", padx=1, pady=1)

        self.max_btn = tk.Button(self.title_bar, text="□", bg="#ffd6e8",
                                 fg="#7a2050", relief="raised", bd=1,
                                 command=self.toggle_maximize,
                                 activebackground="#ffb3d9",
                                 font=("MS Sans Serif", 8, "bold"), width=2)
        self.max_btn.pack(side="right", padx=1, pady=1)

        self.min_btn = tk.Button(self.title_bar, text="_", bg="#ffd6e8",
                                 fg="#7a2050", relief="raised", bd=1,
                                 command=self.minimize,
                                 activebackground="#ffb3d9",
                                 font=("MS Sans Serif", 8, "bold"), width=2)
        self.min_btn.pack(side="right", padx=1, pady=1)

        # Content area
        self.content = tk.Frame(self, bg="#c0c0c0", relief="sunken", bd=2)
        self.content.pack(fill="both", expand=True, padx=2, pady=2)

        # Drag handling
        for w in (self.title_bar, self.title_label):
            w.bind("<Button-1>", self.start_move)
            w.bind("<B1-Motion>", self.do_move)
            w.bind("<Double-Button-1>", lambda e: self.toggle_maximize())

        self.bind("<Button-1>", lambda e: self._focus(), add="+")

        if desktop:
            desktop.register_window(self, title)

    # --------------------------------------------------------------
    def set_title(self, text):
        try:
            self.title_label.config(text=text)
        except Exception:
            pass
        if self.taskbar_btn:
            short = text if len(text) <= 16 else text[:15] + "..."
            try:
                self.taskbar_btn.config(text=short)
            except Exception:
                pass

    def _focus(self):
        try:
            self.lift()
            if self.desktop:
                self.desktop.highlight_taskbar(self)
        except Exception:
            pass

    # --------------------------------------------------------------
    # Dragging
    # --------------------------------------------------------------
    def start_move(self, event):
        if self.maximized:
            return
        self._dx, self._dy = event.x, event.y

    def do_move(self, event):
        if self.maximized:
            return
        self.geometry(
            f"+{self.winfo_x() + event.x - self._dx}"
            f"+{self.winfo_y() + event.y - self._dy}"
        )

    # --------------------------------------------------------------
    # Window state
    # --------------------------------------------------------------
    def minimize(self):
        self.minimized = True
        self.withdraw()
        if self.desktop:
            self.desktop.set_taskbar_state(self, minimized=True)

    def restore(self):
        self.minimized = False
        self.deiconify()
        self.lift()
        self._focus()
        if self.desktop:
            self.desktop.set_taskbar_state(self, minimized=False)

    def toggle_maximize(self):
        if not self.winfo_exists():
            return
        if self.maximized:
            if self._prev_geo:
                self.geometry(self._prev_geo)
            self.maximized = False
            self.max_btn.config(text="□")
        else:
            self._prev_geo = self.geometry()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry(f"{sw}x{sh - TASKBAR_H}+0+0")
            self.maximized = True
            self.max_btn.config(text="❐")

    # --------------------------------------------------------------
    def _close(self):
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        if self.desktop:
            try:
                self.desktop.unregister_window(self)
            except Exception:
                pass
        self.destroy()