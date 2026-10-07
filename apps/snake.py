"""Snake."""
import random
import tkinter as tk

from core.retro_window import RetroWindow
from core.sounds import SOUNDS


class SnakeWindow(RetroWindow):
    CELL, COLS, ROWS = 18, 22, 20

    def __init__(self, master, desktop):
        w = self.CELL * self.COLS + 30
        h = self.CELL * self.ROWS + 100
        super().__init__(master, title="Snake", width=w, height=h,
                         desktop=desktop)

        top = tk.Frame(self.content, bg="#c0c0c0")
        top.pack(fill="x", padx=6, pady=(6, 2))
        tk.Label(top, text="Score:", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(side="left")
        self.score_lbl = tk.Label(top, text="0", bg="#c0c0c0",
                                  font=("MS Sans Serif", 10, "bold"))
        self.score_lbl.pack(side="left", padx=4)
        tk.Button(top, text="New Game", font=("MS Sans Serif", 8),
                  command=self.reset).pack(side="right")

        self.canvas = tk.Canvas(self.content,
                                width=self.CELL * self.COLS,
                                height=self.CELL * self.ROWS,
                                bg="#1a0a1a", highlightthickness=0, bd=0)
        self.canvas.pack(padx=6, pady=6)

        self._job = None
        self.running = False
        self.bind("<Key>", self.on_key)
        self.bind("<Button-1>", lambda e: self.focus_force(), add="+")
        self.after(80, self.focus_force)
        self.reset()

    def reset(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        mx, my = self.COLS // 2, self.ROWS // 2
        self.snake = [(mx, my), (mx - 1, my), (mx - 2, my)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = self._spawn()
        self.score = 0
        self.score_lbl.config(text="0")
        self.game_over = False
        self.running = True
        self.draw()
        self._job = self.after(400, self.tick)

    def _spawn(self):
        occupied = set(self.snake)
        empty = [(x, y) for x in range(self.COLS) for y in range(self.ROWS)
                 if (x, y) not in occupied]
        return random.choice(empty) if empty else None

    def on_key(self, event):
        if self.game_over:
            return
        k = event.keysym.lower()
        m = {"up": (0, -1), "w": (0, -1),
             "down": (0, 1), "s": (0, 1),
             "left": (-1, 0), "a": (-1, 0),
             "right": (1, 0), "d": (1, 0)}
        if k in m:
            d = m[k]
            if (d[0] + self.direction[0], d[1] + self.direction[1]) == (0, 0):
                return
            self.next_direction = d

    def tick(self):
        if not self.running:
            return
        self.direction = self.next_direction
        hx, hy = self.snake[0]
        nx, ny = hx + self.direction[0], hy + self.direction[1]
        if nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS:
            return self.die()
        if (nx, ny) in self.snake[:-1]:
            return self.die()
        self.snake.insert(0, (nx, ny))
        if (nx, ny) == self.food:
            self.score += 10
            self.score_lbl.config(text=str(self.score))
            self.food = self._spawn()
        else:
            self.snake.pop()
        self.draw()
        delay = max(60, 120 - self.score // 5)
        self._job = self.after(delay, self.tick)

    def draw(self):
        self.canvas.delete("all")
        C = self.CELL
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                fill = "#ff9ec7"
            else:
                r = max(0, 158 - int(60 * i / max(1, len(self.snake))))
                g = max(0, 199 - int(30 * i / max(1, len(self.snake))))
                fill = f"#ff{r:02x}{g:02x}"
            self.canvas.create_rectangle(x * C + 1, y * C + 1,
                                         (x + 1) * C - 1, (y + 1) * C - 1,
                                         fill=fill, outline="#c85fa0")
        if self.food:
            fx, fy = self.food
            self.canvas.create_oval(fx * C + 3, fy * C + 3,
                                    (fx + 1) * C - 3, (fy + 1) * C - 3,
                                    fill="#ff69b4", outline="#ffb3d9", width=2)
        if self.game_over:
            self.canvas.create_rectangle(
                0, self.ROWS * C // 2 - 30,
                self.COLS * C, self.ROWS * C // 2 + 30,
                fill="#1a0a1a", outline="#ff69b4", width=2)
            self.canvas.create_text(self.COLS * C // 2, self.ROWS * C // 2,
                                    text=f"GAME OVER  —  Score {self.score}",
                                    fill="#ff69b4",
                                    font=("MS Sans Serif", 12, "bold"))

    def die(self):
        self.running = False
        self.game_over = True
        SOUNDS.error()
        self.draw()

    def _close(self):
        self.running = False
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        super()._close()