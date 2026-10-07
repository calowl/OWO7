"""Dice roller."""
import random
import tkinter as tk

from core.retro_window import RetroWindow
from core.sounds import SOUNDS


class DiceWindow(RetroWindow):
    FACE = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

    def __init__(self, master, desktop):
        super().__init__(master, title="Dice Roller", width=320, height=260,
                         desktop=desktop)
        tk.Label(self.content, text="🎲 Dice Roller 🎲", bg="#c0c0c0",
                 fg="#c85fa0",
                 font=("MS Sans Serif", 12, "bold")).pack(pady=(12, 4))

        count_row = tk.Frame(self.content, bg="#c0c0c0")
        count_row.pack(pady=4)
        tk.Label(count_row, text="Dice:", bg="#c0c0c0",
                 font=("MS Sans Serif", 9)).pack(side="left")
        self.count_var = tk.IntVar(value=2)
        for n in (1, 2, 3, 4, 5, 6):
            tk.Radiobutton(count_row, text=str(n), variable=self.count_var,
                           value=n, bg="#c0c0c0", fg="#7a2050",
                           activebackground="#c0c0c0",
                           selectcolor="#ffd6e8",
                           font=("MS Sans Serif", 8)).pack(side="left")

        self.display = tk.Label(self.content, text="⚀ ⚀", bg="#fff8fc",
                                fg="#c85fa0", font=("Segoe UI Symbol", 42),
                                relief="sunken", bd=2, padx=10, pady=10)
        self.display.pack(pady=10, fill="x", padx=16)

        self.total_lbl = tk.Label(self.content, text="Total: 2",
                                  bg="#c0c0c0", fg="#7a2050",
                                  font=("MS Sans Serif", 10, "bold"))
        self.total_lbl.pack()

        tk.Button(self.content, text="Roll!", width=12,
                  font=("MS Sans Serif", 10, "bold"),
                  bg="#ffd6e8", fg="#7a2050", activebackground="#ffb3d9",
                  command=self.roll).pack(pady=10)

    def roll(self):
        SOUNDS.click()
        n = self.count_var.get()
        rolls = [random.randint(1, 6) for _ in range(n)]
        self.display.config(text=" ".join(self.FACE[r] for r in rolls))
        self.total_lbl.config(
            text=f"Total: {sum(rolls)}   ({', '.join(map(str, rolls))})")