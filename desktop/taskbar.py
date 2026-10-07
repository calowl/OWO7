"""Bottom taskbar: Start button, window buttons, clock."""
import time
import tkinter as tk

from core.state import STATE, TASKBAR_H
from core.sounds import SOUNDS


class Taskbar:
    def __init__(self, root, desktop):
        self.root = root
        self.desktop = desktop

        self.frame = tk.Frame(root, bg="#ffd6e8", height=TASKBAR_H,
                              relief="raised", bd=2)
        self.frame.pack(side="bottom", fill="x")
        self.frame.pack_propagate(False)

        # Start button
        self.start_btn = tk.Button(
            self.frame, text="♥ Start", bg="#ffb3d9", fg="#7a2050",
            relief="raised", bd=2, activebackground="#ff69b4",
            font=("MS Sans Serif", 8, "bold"),
            command=self.desktop.toggle_start_menu)
        self.start_btn.pack(side="left", padx=2, pady=2)

        # Divider
        tk.Frame(self.frame, bg="#c85fa0", width=2).pack(
            side="left", fill="y", padx=2, pady=2)

        # Container for window buttons
        self.windows_frame = tk.Frame(self.frame, bg="#ffd6e8")
        self.windows_frame.pack(side="left", fill="both", expand=True)

        # Clock (pinned to the right)
        self.clock = tk.Label(self.frame, bg="#ffd6e8", fg="#7a2050",
                              font=("MS Sans Serif", 8, "bold"))
        self.clock.pack(side="right", padx=5)

        self._clock_job = None

    # ------------------------------------------------------------------
    #  Clock
    # ------------------------------------------------------------------
    def start_clock(self):
        self.update_clock()

    def update_clock(self):
        if STATE.show_clock:
            self.clock.config(text=time.strftime("%I:%M %p"))
        else:
            self.clock.config(text="")
        try:
            self._clock_job = self.root.after(1000, self.update_clock)
        except Exception:
            self._clock_job = None

    def stop_clock(self):
        if self._clock_job:
            try:
                self.root.after_cancel(self._clock_job)
            except Exception:
                pass
            self._clock_job = None

    # ------------------------------------------------------------------
    #  Window buttons
    # ------------------------------------------------------------------
    def add_window_button(self, win, title):
        short = self._short(title)
        btn = tk.Button(
            self.windows_frame, text=short,
            bg="#ffd6e8", fg="#7a2050",
            relief="raised", bd=2, anchor="w",
            activebackground="#ffb3d9",
            font=("MS Sans Serif", 8), width=16,
            command=lambda w=win: self._click_window(w))
        btn.pack(side="left", padx=1, pady=2)
        win.taskbar_btn = btn
        return btn

    def remove_window_button(self, win):
        btn = getattr(win, "taskbar_btn", None)
        if btn:
            try:
                btn.destroy()
            except Exception:
                pass
            win.taskbar_btn = None

    def set_button_state(self, win, minimized=False):
        btn = getattr(win, "taskbar_btn", None)
        if not btn:
            return
        try:
            btn.config(relief="sunken" if minimized else "raised")
        except Exception:
            pass

    def highlight(self, win):
        for w in self.desktop.windows:
            btn = getattr(w, "taskbar_btn", None)
            if not btn:
                continue
            try:
                if w is win and not w.minimized:
                    btn.config(relief="sunken")
                elif w is not win:
                    btn.config(relief="raised")
            except Exception:
                pass

    def update_button_text(self, win, title):
        btn = getattr(win, "taskbar_btn", None)
        if not btn:
            return
        try:
            btn.config(text=self._short(title))
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _click_window(self, win):
        SOUNDS.click()
        if win.minimized:
            win.restore()
        else:
            win.lift()
            win._focus()

    @staticmethod
    def _short(text, n=16):
        return text if len(text) <= n else text[:n - 1] + "..."