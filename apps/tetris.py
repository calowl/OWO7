"""Tetris."""
import random
import tkinter as tk

from core.retro_window import RetroWindow


class TetrisWindow(RetroWindow):
    COLS, ROWS, CELL = 10, 20, 22
    SHAPES = {
        "I": ([(0, 0), (1, 0), (2, 0), (3, 0)], "#00f0f0"),
        "O": ([(0, 0), (1, 0), (0, 1), (1, 1)], "#f0f000"),
        "T": ([(0, 0), (1, 0), (2, 0), (1, 1)], "#a000f0"),
        "S": ([(1, 0), (2, 0), (0, 1), (1, 1)], "#00f000"),
        "Z": ([(0, 0), (1, 0), (1, 1), (2, 1)], "#f00000"),
        "J": ([(0, 0), (0, 1), (1, 1), (2, 1)], "#0000f0"),
        "L": ([(2, 0), (0, 1), (1, 1), (2, 1)], "#f0a000"),
    }

    def __init__(self, master, desktop):
        W = self.COLS * self.CELL
        H = self.ROWS * self.CELL
        super().__init__(master, title="Tetris", width=W + 180,
                         height=H + 90, desktop=desktop)

        row = tk.Frame(self.content, bg="#c0c0c0")
        row.pack(fill="both", expand=True, padx=4, pady=4)

        self.canvas = tk.Canvas(row, width=W, height=H, bg="#1a0a1a",
                                highlightthickness=0, bd=0)
        self.canvas.pack(side="left")

        side = tk.Frame(row, bg="#c0c0c0")
        side.pack(side="left", fill="y", padx=(8, 0))

        tk.Label(side, text="Score", bg="#c0c0c0", fg="#7a2050",
                 font=("MS Sans Serif", 9, "bold")).pack(anchor="w")
        self.score_lbl = tk.Label(side, text="0", bg="#c0c0c0",
                                  fg="#c85fa0", font=("MS Sans Serif", 14, "bold"))
        self.score_lbl.pack(anchor="w")

        tk.Label(side, text="Lines", bg="#c0c0c0", fg="#7a2050",
                 font=("MS Sans Serif", 9, "bold")).pack(anchor="w", pady=(10, 0))
        self.lines_lbl = tk.Label(side, text="0", bg="#c0c0c0",
                                  fg="#c85fa0", font=("MS Sans Serif", 14, "bold"))
        self.lines_lbl.pack(anchor="w")

        tk.Label(side, text="Next", bg="#c0c0c0", fg="#7a2050",
                 font=("MS Sans Serif", 9, "bold")).pack(anchor="w", pady=(10, 0))
        self.next_canvas = tk.Canvas(side, width=90, height=90, bg="#1a0a1a",
                                     highlightthickness=0, bd=0)
        self.next_canvas.pack(anchor="w")

        tk.Label(side, text="← →  ↓  ↑ rotate\nspace = hard drop",
                 bg="#c0c0c0", fg="#7a2050",
                 font=("MS Sans Serif", 7), justify="left"
                 ).pack(anchor="w", pady=(10, 0))

        tk.Button(side, text="New Game", font=("MS Sans Serif", 8),
                  command=self.reset).pack(anchor="w", pady=(10, 0))

        self.bind("<Key>", self.on_key)
        self.bind("<Button-1>", lambda e: self.focus_force(), add="+")
        self.after(80, self.focus_force)
        self._job = None
        self.reset()

    def reset(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        self.grid = [[None] * self.COLS for _ in range(self.ROWS)]
        self.score = 0
        self.lines = 0
        self.game_over = False
        self.score_lbl.config(text="0")
        self.lines_lbl.config(text="0")
        self.current = None
        self.next_piece = self.random_piece()
        self.spawn_piece()
        self.draw()
        self._job = self.after(500, self.tick)

    def random_piece(self):
        k = random.choice(list(self.SHAPES.keys()))
        coords, color = self.SHAPES[k]
        return {"kind": k, "coords": list(coords), "color": color,
                "x": self.COLS // 2 - 2, "y": 0}

    def spawn_piece(self):
        self.current = self.next_piece
        self.current["x"] = self.COLS // 2 - 2
        self.current["y"] = 0
        self.next_piece = self.random_piece()
        if self.collides(self.current["coords"], self.current["x"], self.current["y"]):
            self.game_over = True

    def collides(self, coords, ox, oy):
        for (x, y) in coords:
            gx, gy = ox + x, oy + y
            if gx < 0 or gx >= self.COLS or gy >= self.ROWS:
                return True
            if gy >= 0 and self.grid[gy][gx] is not None:
                return True
        return False

    def on_key(self, event):
        if self.game_over or not self.current:
            return
        k = event.keysym.lower()
        if k == "left":
            if not self.collides(self.current["coords"], self.current["x"] - 1, self.current["y"]):
                self.current["x"] -= 1
                self.draw()
        elif k == "right":
            if not self.collides(self.current["coords"], self.current["x"] + 1, self.current["y"]):
                self.current["x"] += 1
                self.draw()
        elif k == "down":
            if not self.collides(self.current["coords"], self.current["x"], self.current["y"] + 1):
                self.current["y"] += 1
                self.draw()
        elif k == "up":
            coords = self.current["coords"]
            rotated = [(y, -x) for (x, y) in coords]
            minx = min(x for x, _ in rotated)
            miny = min(y for _, y in rotated)
            rotated = [(x - minx, y - miny) for (x, y) in rotated]
            if not self.collides(rotated, self.current["x"], self.current["y"]):
                self.current["coords"] = rotated
                self.draw()
        elif k == "space":
            while not self.collides(self.current["coords"], self.current["x"], self.current["y"] + 1):
                self.current["y"] += 1
            self.lock_piece()

    def tick(self):
        if self.game_over:
            return
        if not self.collides(self.current["coords"], self.current["x"], self.current["y"] + 1):
            self.current["y"] += 1
        else:
            self.lock_piece()
        self.draw()
        delay = max(120, 500 - self.lines * 15)
        self._job = self.after(delay, self.tick)

    def lock_piece(self):
        for (x, y) in self.current["coords"]:
            gx, gy = self.current["x"] + x, self.current["y"] + y
            if 0 <= gy < self.ROWS and 0 <= gx < self.COLS:
                self.grid[gy][gx] = self.current["color"]
        new_grid = [r for r in self.grid if any(c is None for c in r)]
        cleared = self.ROWS - len(new_grid)
        for _ in range(cleared):
            new_grid.insert(0, [None] * self.COLS)
        self.grid = new_grid
        if cleared:
            self.lines += cleared
            self.score += cleared * 100
            self.score_lbl.config(text=str(self.score))
            self.lines_lbl.config(text=str(self.lines))
        self.spawn_piece()

    def draw(self):
        c = self.canvas
        C = self.CELL
        c.delete("all")
        for y in range(self.ROWS):
            for x in range(self.COLS):
                if self.grid[y][x]:
                    c.create_rectangle(x * C + 1, y * C + 1,
                                       (x + 1) * C - 1, (y + 1) * C - 1,
                                       fill=self.grid[y][x], outline="#0a000a")
        if self.current and not self.game_over:
            for (x, y) in self.current["coords"]:
                gx, gy = self.current["x"] + x, self.current["y"] + y
                if gy >= 0:
                    c.create_rectangle(gx * C + 1, gy * C + 1,
                                       (gx + 1) * C - 1, (gy + 1) * C - 1,
                                       fill=self.current["color"], outline="#0a000a")
        self.next_canvas.delete("all")
        if self.next_piece:
            NC = 18
            for (x, y) in self.next_piece["coords"]:
                self.next_canvas.create_rectangle(x * NC + 10, y * NC + 20,
                                                  (x + 1) * NC + 8, (y + 1) * NC + 18,
                                                  fill=self.next_piece["color"],
                                                  outline="#0a000a")
        if self.game_over:
            c.create_rectangle(0, self.ROWS * C // 2 - 30, self.COLS * C,
                               self.ROWS * C // 2 + 30,
                               fill="#1a0a1a", outline="#ff69b4", width=2)
            c.create_text(self.COLS * C // 2, self.ROWS * C // 2 - 8,
                          text="GAME OVER", fill="#ff69b4",
                          font=("MS Sans Serif", 16, "bold"))
            c.create_text(self.COLS * C // 2, self.ROWS * C // 2 + 14,
                          text=f"Score: {self.score}", fill="white",
                          font=("MS Sans Serif", 9))

    def _close(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        super()._close()