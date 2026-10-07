"""Notepad."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from core.retro_window import RetroWindow
from core.sounds import SOUNDS


class NotepadWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="Untitled - Notepad",
                         width=560, height=420, desktop=desktop)
        self.desktop = desktop
        self.filepath = None
        self.dirty = False

        menu_bar = tk.Frame(self.content, bg="#c0c0c0")
        menu_bar.pack(fill="x")

        def mb(label, builder):
            b = tk.Button(menu_bar, text=label, font=("MS Sans Serif", 8),
                          bg="#c0c0c0", relief="flat", padx=6,
                          command=lambda: builder(b))
            b.pack(side="left")

        mb("File", self.file_menu)
        mb("Edit", self.edit_menu)

        self.text = tk.Text(self.content, bg="#fff8fc", relief="sunken", bd=1,
                            font=("Consolas", 10), wrap="word",
                            undo=True, insertbackground="#c85fa0")
        self.text.pack(fill="both", expand=True, padx=2, pady=(2, 0))
        self.text.bind("<Key>", self.on_typing)

        self.status = tk.Label(self.content, text="Ln 1, Col 1", bg="#c0c0c0",
                               font=("MS Sans Serif", 8), anchor="w")
        self.status.pack(fill="x")
        self.text.bind("<KeyRelease>", self.update_status, add="+")
        self.text.bind("<ButtonRelease-1>", self.update_status, add="+")

    def on_typing(self, e):
        self.dirty = True
        self.update_title()

    def update_title(self):
        name = os.path.basename(self.filepath) if self.filepath else "Untitled"
        self.set_title(f"{'*' if self.dirty else ''}{name} - Notepad")

    def update_status(self, e=None):
        try:
            line, col = self.text.index("insert").split(".")
            self.status.config(text=f"Ln {line}, Col {int(col) + 1}")
        except Exception:
            pass

    def file_menu(self, anchor):
        m = self._popup(anchor)

        def add(label, cmd, sep=False):
            if sep:
                tk.Frame(m, height=1, bg="#808080").pack(fill="x", pady=2)
            tk.Button(m, text=label, anchor="w", bg="#c0c0c0", relief="flat",
                      font=("MS Sans Serif", 8), width=14,
                      command=lambda: (m.destroy(), cmd())
                      ).pack(fill="x", padx=2, pady=1)

        add("New", self.new_file)
        add("Open...", self.open_file)
        add("Save", self.save_file)
        add("Save As...", self.save_as)
        add("", None, sep=True)
        add("Exit", self._close)

    def edit_menu(self, anchor):
        m = self._popup(anchor)

        def add(label, cmd, sep=False):
            if sep:
                tk.Frame(m, height=1, bg="#808080").pack(fill="x", pady=2)
            tk.Button(m, text=label, anchor="w", bg="#c0c0c0", relief="flat",
                      font=("MS Sans Serif", 8), width=14,
                      command=lambda: (m.destroy(), cmd())
                      ).pack(fill="x", padx=2, pady=1)

        def ev(n):
            def go():
                try:
                    self.text.event_generate(n)
                except Exception:
                    pass
            return go

        add("Cut", ev("<<Cut>>"))
        add("Copy", ev("<<Copy>>"))
        add("Paste", ev("<<Paste>>"))
        add("", None, sep=True)
        add("Select All",
            lambda: self.text.tag_add("sel", "1.0", "end"))

    def _popup(self, anchor):
        m = tk.Toplevel(self)
        m.overrideredirect(True)
        m.geometry(f"+{anchor.winfo_rootx()}"
                   f"+{anchor.winfo_rooty() + anchor.winfo_height()}")
        m.configure(bg="#c0c0c0", relief="raised", bd=2)
        m.bind("<FocusOut>", lambda e: m.destroy())
        m.after(50, m.focus_force)
        return m

    def new_file(self):
        self.text.delete("1.0", "end")
        self.filepath = None
        self.dirty = False
        self.update_title()

    def open_file(self):
        p = filedialog.askopenfilename(
            filetypes=[("Text", "*.txt"), ("Python", "*.py"), ("All", "*.*")])
        if not p:
            return
        try:
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)
            self.filepath = p
            self.dirty = False
            self.update_title()
        except Exception as e:
            SOUNDS.error()
            messagebox.showerror("Notepad", f"Could not open:\n{e}")

    def save_file(self):
        if not self.filepath:
            self.save_as()
            return
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", "end-1c"))
            self.dirty = False
            self.update_title()
        except Exception as e:
            SOUNDS.error()
            messagebox.showerror("Notepad", f"Could not save:\n{e}")

    def save_as(self):
        p = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Python", "*.py"), ("All", "*.*")])
        if not p:
            return
        self.filepath = p
        self.save_file()