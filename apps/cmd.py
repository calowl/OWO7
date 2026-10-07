"""Command Prompt."""
import time
import tkinter as tk

from core.retro_window import RetroWindow
from core.state import STATE


def build_fs():
    return {
        "C:": {"type": "drive", "children": {
            "0W07": {"type": "folder", "children": {
                "0W07.py":    {"type": "file"},
                "README.txt": {"type": "file"},
                "assets": {"type": "folder", "children": {
                    "boot.png":   {"type": "file"},
                    "mascots":    {"type": "folder", "children": {}},
                    "sounds":     {"type": "folder", "children": {}},
                    "music":      {"type": "folder", "children": {}},
                    "wallpapers": {"type": "folder", "children": {}},
                }},
            }},
            "Windows": {"type": "folder", "children": {
                "system32": {"type": "folder", "children": {
                    "kernel.dll": {"type": "file"},
                    "user32.dll": {"type": "file"},
                    "gdi32.dll":  {"type": "file"},
                }},
                "notepad.exe":  {"type": "file"},
                "explorer.exe": {"type": "file"},
            }},
            "Program Files": {"type": "folder", "children": {}},
        }},
        "D:": {"type": "drive", "children": {
            "Music":   {"type": "folder", "children": {}},
            "Videos":  {"type": "folder", "children": {}},
            "Backups": {"type": "folder", "children": {}},
        }},
    }


class CommandPromptWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="Command Prompt",
                         width=640, height=420, desktop=desktop)
        self.desktop = desktop
        self.fs = build_fs()
        self.cwd = ["C:"]
        self.history = []
        self.hist_idx = 0

        self.out = tk.Text(self.content, bg="black", fg="#c0c0c0",
                           font=("Consolas", 9), bd=0, relief="flat",
                           wrap="word", state="disabled")
        self.out.pack(fill="both", expand=True, padx=2, pady=(2, 0))

        row = tk.Frame(self.content, bg="black")
        row.pack(fill="x", padx=2, pady=(0, 2))
        self.prompt_lbl = tk.Label(row, text=self.prompt_str(), bg="black",
                                   fg="#ff69b4", font=("Consolas", 9))
        self.prompt_lbl.pack(side="left")
        self.entry = tk.Entry(row, bg="black", fg="#c0c0c0",
                              insertbackground="#ff69b4",
                              font=("Consolas", 9), bd=0, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<Up>", self.hist_up)
        self.entry.bind("<Down>", self.hist_down)
        self.entry.focus_set()
        self.bind("<Button-1>", lambda e: self.entry.focus_set(), add="+")
        self.write("(c) 2007 owlito. Type HELP for commands.\n\n")

    def prompt_str(self):
        return "\\".join(self.cwd) + ">"

    def write(self, s):
        self.out.config(state="normal")
        self.out.insert("end", s)
        self.out.see("end")
        self.out.config(state="disabled")

    def on_enter(self, event):
        cmd = self.entry.get()
        self.entry.delete(0, "end")
        self.write(self.prompt_str() + cmd + "\n")
        if cmd.strip():
            self.history.append(cmd)
            self.hist_idx = len(self.history)
            self.run(cmd.strip())
        self.prompt_lbl.config(text=self.prompt_str())
        return "break"

    def hist_up(self, event):
        if not self.history:
            return "break"
        self.hist_idx = max(0, self.hist_idx - 1)
        self.entry.delete(0, "end")
        self.entry.insert(0, self.history[self.hist_idx])
        return "break"

    def hist_down(self, event):
        if not self.history:
            return "break"
        self.hist_idx = min(len(self.history), self.hist_idx + 1)
        self.entry.delete(0, "end")
        if self.hist_idx < len(self.history):
            self.entry.insert(0, self.history[self.hist_idx])
        return "break"

    def resolve_node(self):
        node = self.fs
        for key in self.cwd:
            node = node[key]["children"]
        return node

    def run(self, cmd):
        parts = cmd.split()
        if not parts:
            return
        c = parts[0].lower()
        args = parts[1:]

        if c == "help":
            self.write("Commands: HELP DIR CD CLS ECHO VER DATE TIME WHOAMI\n")
            self.write("          NOTEPAD CALC PAINT MUSIC STORE SNAKE PONG EXIT\n")
        elif c == "dir":
            node = self.resolve_node()
            path_str = "\\".join(self.cwd)
            self.write(" Directory of " + path_str + "\\\n\n")
            for name in sorted(node.keys()):
                kind = "<DIR>" if node[name]["type"] in ("drive", "folder") else "     "
                self.write(f"  {kind}  {name}\n")
            self.write(f"\n  {len(node)} item(s)\n")
        elif c == "cd":
            if not args:
                self.write("\\".join(self.cwd) + "\n")
                return
            target = args[0]
            if target == "..":
                if len(self.cwd) > 1:
                    self.cwd.pop()
            elif target in (".", "\\"):
                pass
            else:
                node = self.resolve_node()
                match = next((k for k in node
                              if k.lower() == target.lower()
                              and node[k]["type"] in ("drive", "folder")), None)
                if match:
                    self.cwd.append(match)
                else:
                    self.write("The system cannot find the path specified.\n")
        elif c == "cls":
            self.out.config(state="normal")
            self.out.delete("1.0", "end")
            self.out.config(state="disabled")
        elif c == "echo":
            self.write(" ".join(args) + "\n")
        elif c == "ver":
            self.write("0W07 [Version 0.6]\n")
        elif c == "date":
            self.write(time.strftime("%a %m/%d/%Y\n"))
        elif c == "time":
            self.write(time.strftime("%I:%M:%S %p\n"))
        elif c == "whoami":
            self.write(f"0w07\\{STATE.username}\n")
        elif c == "notepad":
            self.desktop.open_notepad()
        elif c in ("calc", "calculator"):
            self.desktop.open_calculator()
        elif c == "paint":
            self.desktop.open_paint()
        elif c in ("music", "player"):
            self.desktop.open_music_player()
        elif c in ("store", "shop"):
            self.desktop.open_store()
        elif c == "snake":
            self.desktop.open_snake()
        elif c == "pong":
            self.desktop.open_pong()
        elif c == "doom":
            self.desktop.open_doom()
        elif c == "exit":
            self._close()
        else:
            self.write(f"'{parts[0]}' is not recognized.\n")