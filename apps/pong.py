"""Pong."""
import random
import tkinter as tk

from core.retro_window import RetroWindow


class PongWindow(RetroWindow):
    W, H = 560, 380
    PW, PH, BALL, WIN_SCORE = 10, 60, 12, 7

    def __init__(self, master, desktop):
        super().__init__(master, title="Pong", width=self.W + 20,
                         height=self.H + 90, desktop=desktop)
        self._job = None
        self.running = False
        self.player_score = 0
        self.ai_score = 0
        self.keys = set()

        top = tk.Frame(self.content, bg="#c0c0c0")
        top.pack(fill="x", padx=6, pady=(4, 0))
        self.score_lbl = tk.Label(top, text="0   :   0", bg="#c0c0c0",
                                  font=("MS Sans Serif", 14, "bold"))
        self.score_lbl.pack(side="left")
        tk.Label(top, text="W/S or arrows · First to 7 wins", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(side="right")

        self.canvas = tk.Canvas(self.content, width=self.W, height=self.H,
                                bg="#1a0a1a", highlightthickness=0)
        self.canvas.pack(padx=6, pady=6)

        self.bind("<Key>", self.on_key)
        self.bind("<KeyRelease>", self.on_key_release)
        self.bind("<Button-1>", lambda e: self.focus_force(), add="+")
        self.after(80, self.focus_force)
        self.new_round(first=True)

    def new_round(self, first=False):
        if not first and self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        self.py = self.H / 2
        self.ay = self.H / 2
        self.bx = self.W / 2
        self.by = self.H / 2
        dx = random.choice([-1, 1])
        dy = random.choice([-1, 1]) * random.uniform(0.4, 0.9)
        self.bdx = dx * 5
        self.bdy = dy * 5
        self.running = True
        self.draw()
        self._job = self.after(30, self.tick)

    def on_key(self, event):
        k = event.keysym.lower()
        if k in ("up", "w", "down", "s"):
            self.keys.add(k)
            return "break"

    def on_key_release(self, event):
        self.keys.discard(event.keysym.lower())

    def tick(self):
        if not self.running:
            return
        if "up" in self.keys or "w" in self.keys:
            self.py = max(self.PH / 2, self.py - 8)
        if "down" in self.keys or "s" in self.keys:
            self.py = min(self.H - self.PH / 2, self.py + 8)

        diff = self.by - self.ay
        self.ay += max(-5, min(5, diff * 0.12))
        self.ay = max(self.PH / 2, min(self.H - self.PH / 2, self.ay))

        self.bx += self.bdx
        self.by += self.bdy
        if self.by - self.BALL / 2 <= 0 or self.by + self.BALL / 2 >= self.H:
            self.bdy = -self.bdy

        if (self.bx - self.BALL / 2 <= 20 + self.PW / 2
                and abs(self.by - self.py) < self.PH / 2):
            self.bdx = abs(self.bdx) * 1.05
            self.bdy += (self.by - self.py) * 0.1
            self.bx = 20 + self.PW / 2 + self.BALL / 2
        if (self.bx + self.BALL / 2 >= self.W - 20 - self.PW / 2
                and abs(self.by - self.ay) < self.PH / 2):
            self.bdx = -abs(self.bdx) * 1.05
            self.bdy += (self.by - self.ay) * 0.1
            self.bx = self.W - 20 - self.PW / 2 - self.BALL / 2

        if self.bx < 0:
            self.ai_score += 1
            return self.end_round()
        if self.bx > self.W:
            self.player_score += 1
            return self.end_round()

        self.draw()
        self._job = self.after(16, self.tick)

    def draw(self):
        c = self.canvas
        c.delete("all")
        for y in range(0, self.H, 20):
            c.create_line(self.W / 2, y, self.W / 2, y + 10,
                          fill="#4a2a4a", width=2)
        c.create_rectangle(20 - self.PW / 2, self.py - self.PH / 2,
                           20 + self.PW / 2, self.py + self.PH / 2,
                           fill="#ff9ec7", outline="")
        c.create_rectangle(self.W - 20 - self.PW / 2, self.ay - self.PH / 2,
                           self.W - 20 + self.PW / 2, self.ay + self.PH / 2,
                           fill="#c85fa0", outline="")
        c.create_oval(self.bx - self.BALL / 2, self.by - self.BALL / 2,
                      self.bx + self.BALL / 2, self.by + self.BALL / 2,
                      fill="#ffd6e8", outline="#ff69b4", width=2)
        self.score_lbl.config(text=f"{self.player_score}   :   {self.ai_score}")

    def end_round(self):
        self.running = False
        self.draw()
        winner = None
        if self.player_score >= self.WIN_SCORE:
            winner = "You win!"
        elif self.ai_score >= self.WIN_SCORE:
            winner = "CPU wins!"
        if winner:
            self.canvas.create_rectangle(self.W / 2 - 110, self.H / 2 - 30,
                                         self.W / 2 + 110, self.H / 2 + 30,
                                         fill="#1a0a1a", outline="#ff69b4",
                                         width=2)
            self.canvas.create_text(self.W / 2, self.H / 2, text=winner,
                                    fill="#ff69b4",
                                    font=("MS Sans Serif", 18, "bold"))
            self.after(2500, self._reset)
        else:
            self.after(800, self.new_round)

    def _reset(self):
        self.player_score = 0
        self.ai_score = 0
        self.new_round(first=True)

    def _close(self):
        self.running = False
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        super()._close()