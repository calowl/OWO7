"""0W07 Store — install/uninstall fake apps."""
import tkinter as tk
from tkinter import messagebox

from core.state import STATE, persist_state
from core.sounds import SOUNDS
from core.retro_window import RetroWindow


STORE_APPS = [
    {
        "id": "tetris",
        "name": "Tetris",
        "icon": "🧱", "pastel": "#ffd6e8", "accent": "✨",
        "description": "Stack falling blocks and clear lines.",
        "size": "12 KB", "category": "Games",
    },
    {
        "id": "clock",
        "name": "Clock",
        "icon": "🕐", "pastel": "#d4f0ff", "accent": "⏰",
        "description": "A cute analog clock with live hands.",
        "size": "4 KB", "category": "Utilities",
    },
    {
        "id": "dice",
        "name": "Dice Roller",
        "icon": "🎲", "pastel": "#fff5b8", "accent": "✨",
        "description": "Roll 1-6 dice. Great for games.",
        "size": "2 KB", "category": "Utilities",
    },
]


def get_store_app(app_id):
    for a in STORE_APPS:
        if a["id"] == app_id:
            return a
    return None


class StoreWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="0W07 Store", width=620, height=460,
                         desktop=desktop)
        self.desktop = desktop

        header = tk.Frame(self.content, bg="#fff0f5")
        header.pack(fill="x")
        tk.Label(header, text="🛍 0W07 Store 🛍", bg="#fff0f5", fg="#c85fa0",
                 font=("MS Sans Serif", 12, "bold")).pack(pady=4)

        body = tk.Frame(self.content, bg="#c0c0c0")
        body.pack(fill="both", expand=True, padx=4, pady=4)

        side = tk.Frame(body, bg="#c0c0c0", width=120)
        side.pack(side="left", fill="y", padx=(0, 4))
        side.pack_propagate(False)
        tk.Label(side, text="Categories", bg="#c0c0c0", fg="#7a2050",
                 font=("MS Sans Serif", 8, "bold")).pack(anchor="w")
        side_inner = tk.Frame(side, bg="#808080", bd=2, relief="sunken")
        side_inner.pack(fill="both", expand=True)
        self.cat_list = tk.Listbox(side_inner, bg="white", fg="#7a2050",
                                   font=("MS Sans Serif", 9),
                                   activestyle="none",
                                   selectbackground="#ffb3d9",
                                   selectforeground="#7a2050",
                                   bd=0, highlightthickness=0)
        self.cat_list.pack(fill="both", expand=True)
        self.cat_list.bind("<<ListboxSelect>>", lambda e: self.refresh())

        self.categories = ["All"] + sorted({a["category"] for a in STORE_APPS})
        for c in self.categories:
            self.cat_list.insert(tk.END, c)
        self.cat_list.selection_set(0)

        right = tk.Frame(body, bg="#c0c0c0")
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Available Apps", bg="#c0c0c0", fg="#7a2050",
                 font=("MS Sans Serif", 8, "bold")).pack(anchor="w")
        list_wrap = tk.Frame(right, bg="#808080", bd=2, relief="sunken")
        list_wrap.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(list_wrap, bg="white", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(list_wrap, command=self.canvas.yview)
        sb.pack(side="right", fill="y")
        self.canvas.config(yscrollcommand=sb.set)
        self.inner = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.status = tk.Label(self.content, text="", bg="#c0c0c0",
                               fg="#7a2050", font=("MS Sans Serif", 8),
                               anchor="w")
        self.status.pack(fill="x", padx=6, pady=(0, 4))
        self.refresh()

    def current_category(self):
        sel = self.cat_list.curselection()
        if not sel:
            return "All"
        return self.categories[sel[0]]

    def refresh(self):
        for w in self.inner.winfo_children():
            w.destroy()
        cat = self.current_category()
        for app in STORE_APPS:
            if cat != "All" and app["category"] != cat:
                continue
            self._build_card(app)
        installed_count = len(STATE.installed_apps)
        self.status.config(text=f"{installed_count} app(s) installed")

    def _build_card(self, app):
        card = tk.Frame(self.inner, bg="white", bd=1, relief="groove")
        card.pack(fill="x", padx=6, pady=4)

        left = tk.Frame(card, bg="white")
        left.pack(side="left", padx=8, pady=8)
        cv = tk.Canvas(left, width=52, height=52, bg="white",
                       highlightthickness=0)
        cv.pack()
        cv.create_oval(2, 2, 50, 50, fill=app["pastel"],
                       outline="#ffffff", width=2)
        cv.create_text(26, 26, text=app["icon"],
                       font=("Segoe UI Emoji", 20))

        mid = tk.Frame(card, bg="white")
        mid.pack(side="left", fill="both", expand=True, padx=4, pady=8)
        tk.Label(mid, text=app["name"], bg="white", fg="#7a2050",
                 font=("MS Sans Serif", 10, "bold"),
                 anchor="w").pack(fill="x")
        tk.Label(mid, text=app["description"], bg="white", fg="#555555",
                 font=("MS Sans Serif", 8), anchor="w",
                 wraplength=280, justify="left").pack(fill="x")
        tk.Label(mid, text=f"{app['category']}  ·  {app['size']}",
                 bg="white", fg="#a04878",
                 font=("MS Sans Serif", 7),
                 anchor="w").pack(fill="x", pady=(2, 0))

        right = tk.Frame(card, bg="white")
        right.pack(side="right", padx=8)
        installed = app["id"] in STATE.installed_apps

        if installed:
            tk.Button(right, text="Play", width=10,
                      font=("MS Sans Serif", 9, "bold"),
                      bg="#ffb3d9", fg="#7a2050",
                      activebackground="#ff69b4",
                      command=lambda a=app: self.launch(a)
                      ).pack(pady=2)
            tk.Button(right, text="Uninstall", width=10,
                      font=("MS Sans Serif", 8),
                      bg="#ffd6e8", fg="#7a2050",
                      activebackground="#ffb3d9",
                      command=lambda a=app: self.uninstall(a)
                      ).pack(pady=2)
        else:
            tk.Button(right, text="Install", width=10,
                      font=("MS Sans Serif", 9, "bold"),
                      bg="#c8f5c8", fg="#2a5a2a",
                      activebackground="#a0e0a0",
                      command=lambda a=app: self.install(a)
                      ).pack(pady=2)

    def install(self, app):
        SOUNDS.click()
        self.status.config(text=f"Downloading {app['name']}...")

        def done():
            STATE.installed_apps.add(app["id"])
            persist_state()
            self.desktop.refresh_desktop()
            self.status.config(text=f"Installed {app['name']}!")
            self.refresh()

        self.after(700, done)

    def uninstall(self, app):
        SOUNDS.click()
        if not messagebox.askyesno("Uninstall",
                                   f"Uninstall {app['name']}?"):
            return
        STATE.installed_apps.discard(app["id"])
        persist_state()
        self.desktop.refresh_desktop()
        self.status.config(text=f"Uninstalled {app['name']}.")
        self.refresh()

    def launch(self, app):
        SOUNDS.click()
        launcher = getattr(self.desktop, f"open_{app['id']}", None)
        if launcher:
            launcher()
        else:
            SOUNDS.error()
            self.status.config(text=f"Cannot launch {app['name']}")