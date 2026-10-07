"""Calculator."""
import tkinter as tk

from core.retro_window import RetroWindow
from core.sounds import SOUNDS


class CalculatorWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="Calculator", width=220, height=280,
                         desktop=desktop)

        self.display = tk.Entry(self.content, font=("MS Sans Serif", 12),
                                justify="right", relief="sunken", bd=2,
                                bg="#fff8fc", fg="#7a2050",
                                insertbackground="#c85fa0")
        self.display.pack(fill="x", padx=4, pady=4)

        grid = tk.Frame(self.content, bg="#c0c0c0")
        grid.pack(expand=True, fill="both", padx=4, pady=4)

        keys = [["7", "8", "9", "/"],
                ["4", "5", "6", "*"],
                ["1", "2", "3", "-"],
                ["0", ".", "=", "+"]]
        for r, row in enumerate(keys):
            for c, k in enumerate(row):
                tk.Button(grid, text=k, width=4, height=2,
                          font=("MS Sans Serif", 9),
                          command=lambda ch=k: self.press(ch)
                          ).grid(row=r, column=c, padx=1, pady=1)

        tk.Button(self.content, text="C", font=("MS Sans Serif", 9),
                  command=lambda: self.press("C")
                  ).pack(fill="x", padx=4, pady=(0, 4))

    def press(self, char):
        if char == "=":
            try:
                r = str(eval(self.display.get()))
                self.display.delete(0, tk.END)
                self.display.insert(0, r)
            except Exception:
                SOUNDS.error()
                self.display.delete(0, tk.END)
                self.display.insert(0, "error")
        elif char == "C":
            self.display.delete(0, tk.END)
        else:
            self.display.insert(tk.END, char)