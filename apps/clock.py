"""Analog clock."""
import math
import time
import tkinter as tk

from core.retro_window import RetroWindow


class ClockWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="Clock", width=280, height=320,
                         desktop=desktop)
        self.canvas = tk.Canvas(self.content, width=240, height=240,
                                bg="#fff0f5", highlightthickness=0, bd=0)
        self.canvas.pack(pady=10)
        self.date_lbl = tk.Label(self.content, text="", bg="#c0c0c0",
                                 fg="#7a2050", font=("MS Sans Serif", 9, "bold"))
        self.date_lbl.pack(pady=(0, 8))
        self._job = None
        self.tick()

    def tick(self):
        if not self.winfo_exists():
            return
        c = self.canvas
        c.delete("all")
        cx, cy, r = 120, 120, 100
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      fill="#ffd6e8", outline="#c85fa0", width=3)
        c.create_oval(cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8,
                      fill="#fff8fc", outline="")
        for i in range(12):
            ang = i * 30 * math.pi / 180
            x1 = cx + (r - 18) * math.sin(ang)
            y1 = cy - (r - 18) * math.cos(ang)
            x2 = cx + (r - 8) * math.sin(ang)
            y2 = cy - (r - 8) * math.cos(ang)
            c.create_line(x1, y1, x2, y2, fill="#c85fa0", width=2)

        t = time.localtime()
        h, m, s = t.tm_hour % 12, t.tm_min, t.tm_sec
        for ang_deg, length, width, color in [
            ((h + m / 60) * 30, 50, 6, "#7a2050"),
            ((m + s / 60) * 6, 70, 4, "#c85fa0"),
            (s * 6, 80, 2, "#ff69b4"),
        ]:
            ang = ang_deg * math.pi / 180
            x2 = cx + length * math.sin(ang)
            y2 = cy - length * math.cos(ang)
            c.create_line(cx, cy, x2, y2, fill=color, width=width,
                          capstyle="round")

        c.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill="#c85fa0", outline="")
        self.date_lbl.config(text=time.strftime("%A, %B %d, %Y"))
        self._job = self.after(1000, self.tick)

    def _close(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        super()._close()