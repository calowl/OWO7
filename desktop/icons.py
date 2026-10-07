"""Desktop icon grid."""
import tkinter as tk

from core.state import STATE
from core.sounds import SOUNDS
from apps.store import STORE_APPS, get_store_app


# (label, emoji, pastel, accent, method-name-on-desktop)
BUILTIN_ICONS = [
    ("My Computer", "🖥",  "#ffd6e8", "✨", "open_file_explorer"),
    ("Store",       "🛍",  "#ffd4e8", "♥",  "open_store"),
    ("Music",       "🎧", "#ffd4e8", "♪",  "open_music_player"),
    ("Notepad",     "📝", "#ffe4b5", "💕", "open_notepad"),
    ("Paint",       "🎨", "#e0d4ff", "🌸", "open_paint"),
    ("Command",     "💻", "#d4f0ff", "⭐", "open_cmd"),
    ("Calculator",  "🧮", "#fff5b8", "✨", "open_calculator"),
    ("Snake",       "🐍", "#c8f5c8", "💚", "open_snake"),
    ("Pong",        "🏓", "#ffd4d4", "💗", "open_pong"),
    ("Settings",    "⚙",  "#e8e8ff", "🌸", "open_settings"),
    ("Recycle Bin", "🗑",  "#ffd6e8", "💫", "open_recycle"),
]


class IconGrid:
    """Manages the icons painted directly on the desktop background."""

    def __init__(self, root, desktop):
        self.root = root
        self.desktop = desktop
        self.canvases = []
        self.selected = None

    # ------------------------------------------------------------------
    def build(self):
        """Wipe and re-draw every icon."""
        self._destroy_all()

        icons = list(BUILTIN_ICONS)

        # Add installed Store apps after the built-ins
        for app_id in sorted(STATE.installed_apps):
            app = get_store_app(app_id)
            if not app:
                continue
            method = f"open_{app_id}"
            if hasattr(self.desktop, method):
                icons.append((app["name"], app["icon"], app["pastel"],
                              app["accent"], method))

        margin_x, margin_y = 20, 20
        dx, dy = 100, 90
        per_row = max(
            1,
            (self.root.winfo_screenwidth() - margin_x * 2) // dx)

        for i, (label, emoji, pastel, accent, method_name) in enumerate(icons):
            x = margin_x + (i % per_row) * dx
            y = margin_y + (i // per_row) * dy
            self._draw_icon(x, y, label, emoji, pastel, accent, method_name)

    def _draw_icon(self, x, y, label, emoji, pastel, accent, method_name):
        cv = tk.Canvas(self.root, width=90, height=80,
                       bg=STATE.desktop_color, highlightthickness=0, bd=0)
        cv.place(x=x, y=y)

        # The selection rectangle (hidden until the icon is clicked)
        cv._bg_rect = cv.create_rectangle(0, 0, 90, 80, fill="", outline="")

        # Round pastel badge behind the emoji
        cv.create_oval(20, 4, 70, 54, fill=pastel,
                       outline="#ffffff", width=2)
        cv.create_text(45, 30, text=emoji, font=("Segoe UI Emoji", 22))
        cv.create_text(72, 10, text=accent, font=("Segoe UI Emoji", 9))

        # Label — shadow + foreground for readability on any color
        cv.create_text(46, 67, text=label, fill="#003333",
                       font=("MS Sans Serif", 8, "bold"),
                       width=88, justify="center")
        cv.create_text(45, 66, text=label, fill="white",
                       font=("MS Sans Serif", 8),
                       width=88, justify="center")

        def on_click(e, c=cv):
            self.select(c)

        def on_double(e, name=method_name):
            SOUNDS.click()
            method = getattr(self.desktop, name, None)
            if method:
                method()

        cv.bind("<Button-1>", on_click)
        cv.bind("<Double-Button-1>", on_double)
        self.canvases.append(cv)

    # ------------------------------------------------------------------
    def select(self, canvas):
        if self.selected and self.selected is not canvas:
            try:
                self.selected.itemconfig(self.selected._bg_rect, fill="")
            except Exception:
                pass
        self.selected = canvas
        try:
            canvas.itemconfig(canvas._bg_rect,
                              fill="#c85fa0", outline="#ffffff")
        except Exception:
            pass

    def deselect(self, event=None):
        if self.selected is None:
            return
        w = event.widget if event else None
        if w in self.canvases:
            return
        try:
            self.selected.itemconfig(self.selected._bg_rect,
                                     fill="", outline="")
        except Exception:
            pass
        self.selected = None

    def recolor(self, color):
        for cv in self.canvases:
            try:
                cv.configure(bg=color)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def _destroy_all(self):
        for cv in self.canvases:
            try:
                cv.destroy()
            except Exception:
                pass
        self.canvases = []
        self.selected = None