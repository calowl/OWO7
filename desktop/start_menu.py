"""Start button menu + Programs submenu."""
import tkinter as tk

from core.state import STATE, TASKBAR_H
from core.sounds import SOUNDS


class StartMenu:
    """Owns the Start menu toplevel and its Programs submenu."""

    MENU_ITEMS = ["Programs", "Store", "Documents", "Settings",
                  "Find", "Help", "Run...", "Shut Down..."]

    # Programs submenu: (label, method name on the desktop)
    PROGRAMS = [
        ("Music Player",  "open_music_player"),
        ("Notepad",       "open_notepad"),
        ("Paint",         "open_paint"),
        ("Command Prompt","open_cmd"),
        ("Calculator",    "open_calculator"),
        ("File Explorer", "open_file_explorer"),
        ("Snake",         "open_snake"),
        ("Pong",          "open_pong"),
    ]

    def __init__(self, root, desktop):
        self.root = root
        self.desktop = desktop
        self.menu = None
        self.programs = None

    # ------------------------------------------------------------------
    def toggle(self):
        SOUNDS.click()
        if self.menu:
            self.close()
        else:
            self.open()

    def open(self):
        if self.menu:
            return

        m = tk.Toplevel(self.root)
        m.overrideredirect(True)
        sh = self.root.winfo_screenheight()
        menu_h = 320
        y = max(0, sh - TASKBAR_H - menu_h)
        m.geometry(f"200x{menu_h}+0+{y}")
        m.configure(bg="#ffd6e8", relief="raised", bd=2)
        self.menu = m

        # Header strip
        header = tk.Frame(m, bg="#c85fa0", height=30)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="♥ 0W07 ♥", bg="#c85fa0", fg="white",
                 font=("MS Sans Serif", 10, "bold")).pack(side="left", padx=5)
        tk.Label(header, text=STATE.username, bg="#c85fa0", fg="#ffd6e8",
                 font=("MS Sans Serif", 8)).pack(side="right", padx=5)

        for name in self.MENU_ITEMS:
            tk.Button(m, text=name, anchor="w",
                      bg="#ffd6e8", fg="#7a2050",
                      relief="flat", activebackground="#ffb3d9",
                      font=("MS Sans Serif", 8),
                      command=lambda n=name: self.item_clicked(n)
                      ).pack(fill="x", padx=2, pady=1)

    def close(self):
        self.close_programs()
        if self.menu:
            try:
                self.menu.destroy()
            except Exception:
                pass
            self.menu = None

    def close_programs(self):
        if self.programs:
            try:
                self.programs.destroy()
            except Exception:
                pass
            self.programs = None

    # ------------------------------------------------------------------
    def item_clicked(self, name):
        SOUNDS.click()

        # Need the geometry of the main menu before we destroy it
        sx = self.menu.winfo_x()
        sy = self.menu.winfo_y()
        sw = self.menu.winfo_width()

        self.close()

        method_map = {
            "Store":      "open_store",
            "Documents":  "open_documents",
            "Settings":   "open_settings",
            "Find":       "open_find",
            "Help":       "open_help",
            "Run...":     "open_run",
            "Shut Down...": "open_shutdown",
        }

        if name == "Programs":
            self.open_programs(sx + sw, sy + 40)
            return

        method_name = method_map.get(name)
        if method_name:
            method = getattr(self.desktop, method_name, None)
            if method:
                method()

    def open_programs(self, x, y):
        sm = tk.Toplevel(self.root)
        sm.overrideredirect(True)
        sm.geometry(f"180x240+{x}+{y}")
        sm.configure(bg="#ffd6e8", relief="raised", bd=2)
        self.programs = sm

        for label, method_name in self.PROGRAMS:
            def launch(m=method_name):
                SOUNDS.click()
                self.close_programs()
                method = getattr(self.desktop, m, None)
                if method:
                    method()

            tk.Button(sm, text=label, anchor="w",
                      bg="#ffd6e8", fg="#7a2050",
                      relief="flat", activebackground="#ffb3d9",
                      font=("MS Sans Serif", 8),
                      command=launch
                      ).pack(fill="x", padx=2, pady=1)