"""Paint."""
import tkinter as tk

from core.retro_window import RetroWindow


class PaintWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="untitled - Paint", width=640, height=480,
                         desktop=desktop)
        self.color = "#000000"
        self.brush = 3
        self.tool = "pencil"
        self.last = None
        self.start_pos = None
        self.preview_id = None

        toolbar = tk.Frame(self.content, bg="#c0c0c0")
        toolbar.pack(fill="x")

        tools = [("✏", "pencil"), ("╱", "line"), ("▭", "rect"),
                 ("◯", "ellipse"), ("⌫", "eraser")]
        self.tool_btns = {}
        for icon, name in tools:
            b = tk.Button(toolbar, text=icon, width=2,
                          font=("MS Sans Serif", 10),
                          relief="sunken" if name == "pencil" else "raised",
                          command=lambda n=name: self.set_tool(n))
            b.pack(side="left", padx=1, pady=2)
            self.tool_btns[name] = b

        tk.Frame(toolbar, bg="#808080", width=2).pack(side="left", fill="y",
                                                     padx=4, pady=2)
        for c in ["#000000", "#ffffff", "#ff0000", "#00ff00", "#0000ff",
                  "#ffff00", "#ff00ff", "#00ffff", "#ff8000", "#800080"]:
            tk.Button(toolbar, bg=c, width=2, height=1, bd=2, relief="raised",
                      command=lambda h=c: self.set_color(h)
                      ).pack(side="left", padx=1, pady=2)

        tk.Frame(toolbar, bg="#808080", width=2).pack(side="left", fill="y",
                                                     padx=4, pady=2)
        self.brush_btns = {}
        for sz in (1, 3, 6, 12):
            b = tk.Button(toolbar, text=str(sz), width=2,
                          font=("MS Sans Serif", 7),
                          relief="sunken" if sz == 3 else "raised",
                          command=lambda s=sz: self.set_brush(s))
            b.pack(side="left", padx=1, pady=2)
            self.brush_btns[sz] = b

        tk.Button(toolbar, text="Clear", font=("MS Sans Serif", 8),
                  command=self.clear).pack(side="right", padx=4, pady=2)

        cf = tk.Frame(self.content, bg="#808080", bd=2, relief="sunken")
        cf.pack(fill="both", expand=True, padx=4, pady=4)
        self.canvas = tk.Canvas(cf, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def set_tool(self, name):
        self.tool = name
        for n, b in self.tool_btns.items():
            b.config(relief="sunken" if n == name else "raised")

    def set_color(self, c):
        self.color = c

    def set_brush(self, s):
        self.brush = s
        for v, b in self.brush_btns.items():
            b.config(relief="sunken" if v == s else "raised")

    def clear(self):
        self.canvas.delete("all")

    def on_press(self, e):
        self.last = (e.x, e.y)
        self.start_pos = (e.x, e.y)
        self.preview_id = None
        if self.tool in ("pencil", "eraser"):
            self.draw_point(e.x, e.y)

    def draw_point(self, x, y):
        r = self.brush / 2
        fill = "white" if self.tool == "eraser" else self.color
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill=fill, outline=fill)

    def on_drag(self, e):
        if self.tool in ("pencil", "eraser"):
            x0, y0 = self.last
            fill = "white" if self.tool == "eraser" else self.color
            self.canvas.create_line(x0, y0, e.x, e.y, fill=fill,
                                    width=self.brush,
                                    capstyle="round", smooth=True)
            self.last = (e.x, e.y)
        else:
            if self.preview_id:
                self.canvas.delete(self.preview_id)
            sx, sy = self.start_pos
            if self.tool == "line":
                self.preview_id = self.canvas.create_line(
                    sx, sy, e.x, e.y, fill=self.color, width=self.brush)
            elif self.tool == "rect":
                self.preview_id = self.canvas.create_rectangle(
                    sx, sy, e.x, e.y, outline=self.color, width=self.brush)
            elif self.tool == "ellipse":
                self.preview_id = self.canvas.create_oval(
                    sx, sy, e.x, e.y, outline=self.color, width=self.brush)

    def on_release(self, e):
        self.preview_id = None
        self.last = None