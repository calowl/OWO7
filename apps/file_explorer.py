"""File explorer — fake filesystem."""
import tkinter as tk

from core.retro_window import RetroWindow
from core.sounds import SOUNDS
from apps.cmd import build_fs


class FileExplorerWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="My Computer",
                         width=520, height=380, desktop=desktop)
        self.fs = build_fs()
        self.path = []

        bar = tk.Frame(self.content, bg="#c0c0c0")
        bar.pack(fill="x", padx=4, pady=(4, 2))
        tk.Button(bar, text="Up", font=("MS Sans Serif", 8),
                  command=self.go_up).pack(side="left")
        tk.Button(bar, text="Refresh", font=("MS Sans Serif", 8),
                  command=self.refresh).pack(side="left", padx=4)
        self.addr = tk.Label(bar, text="My Computer", bg="white", anchor="w",
                             relief="sunken", bd=1,
                             font=("MS Sans Serif", 8))
        self.addr.pack(side="left", fill="x", expand=True, padx=6)

        body = tk.Frame(self.content, bg="#c0c0c0")
        body.pack(fill="both", expand=True, padx=4, pady=4)
        self.listbox = tk.Listbox(body, font=("MS Sans Serif", 9), bg="white",
                                  relief="sunken", bd=1, activestyle="none",
                                  selectbackground="#ffb3d9")
        self.listbox.pack(fill="both", expand=True, side="left")
        self.listbox.bind("<Double-Button-1>", self.on_double)
        sb = tk.Scrollbar(body, command=self.listbox.yview)
        sb.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=sb.set)

        self.status = tk.Label(self.content, text="", bg="#c0c0c0",
                               font=("MS Sans Serif", 8), anchor="w")
        self.status.pack(fill="x", padx=6)
        self.refresh()

    def current_node(self):
        node = self.fs
        for k in self.path:
            node = node[k]["children"]
        return node

    def full_path_str(self):
        return ("My Computer"
                + ("" if not self.path else "\\" + "\\".join(self.path)))

    def refresh(self):
        self.listbox.delete(0, tk.END)
        node = self.current_node()
        self.addr.config(text=self.full_path_str())
        self.items = sorted(node.keys())
        for name in self.items:
            meta = node[name]
            prefix = self.icon_for(meta["type"], name)
            self.listbox.insert(tk.END, f"{prefix}  {name}")
        self.status.config(text=f"{len(self.items)} item(s)")

    @staticmethod
    def icon_for(kind, name):
        if kind == "drive":
            return "[D]"
        if kind == "folder":
            return "[+]"
        if name.endswith((".png", ".gif", ".jpg", ".jpeg")):
            return "[I]"
        if name.endswith((".mp3", ".ogg", ".wav", ".flac")):
            return "[♪]"
        if name.endswith(".py"):
            return "[P]"
        if name.endswith(".txt"):
            return "[T]"
        return "[F]"

    def on_double(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.items[sel[0]]
        meta = self.current_node()[name]
        if meta["type"] in ("folder", "drive"):
            self.path.append(name)
            self.refresh()
        else:
            SOUNDS.error()
            self.status.config(text=f"Cannot open {name}")

    def go_up(self):
        if self.path:
            self.path.pop()
            self.refresh()