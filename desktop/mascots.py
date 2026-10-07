"""Desktop mascots — clickable sprites that show anime facts."""
import os
import random
import tkinter as tk

from core.state import STATE, MASCOTS_DIR, TASKBAR_H
from core.sounds import SOUNDS


class MascotManager:
    FACTS = [
        "Studio Ghibli was founded in 1985 by Hayao Miyazaki and Isao Takahata.",
        "The first anime ever made was 'Katsudoshashin', around 1907.",
        "'Anime' comes from the English word 'animation'.",
        "One Piece has been running since 1997 and has over 1000 chapters.",
        "Spirited Away won the Academy Award for Best Animated Feature in 2003.",
        "Akira (1988) is credited with bringing anime to the West.",
        "Sailor Moon popularized the magical girl genre worldwide in the 90s.",
        "The longest-running anime is Sazae-san, on air since 1969.",
        "Voice actors in Japan are called 'seiyuu'.",
        "Fullmetal Alchemist: Brotherhood is one of the highest-rated anime of all time.",
        "Demon Slayer: Mugen Train was the highest-grossing anime film ever in 2020.",
        "Attack on Titan's author based the walls on his hometown.",
        "Anime openings are called 'OPs', endings are 'EDs'.",
        "The word 'otaku' originally meant 'your home' in Japanese.",
        "Neon Genesis Evangelion's director struggled with depression while making it.",
        "Hayao Miyazaki personally redraws thousands of frames in his films.",
    ]

    def __init__(self, root):
        self.root = root
        self.sprites = []
        self.images = []
        self.reload_images()

    def reload_images(self):
        self.images = []
        if os.path.isdir(MASCOTS_DIR):
            for name in sorted(os.listdir(MASCOTS_DIR)):
                if name.lower().endswith((".png", ".gif")):
                    try:
                        self.images.append(
                            tk.PhotoImage(file=os.path.join(MASCOTS_DIR, name)))
                    except Exception as e:
                        print("bad mascot image", name, e)

    def spawn(self, count=3):
        self.clear()
        w = max(self.root.winfo_width(), 800)
        h = max(self.root.winfo_height(), 600)
        for _ in range(count):
            if self.images:
                img = random.choice(self.images)
                lbl = tk.Label(self.root, image=img, bd=0,
                               bg=STATE.desktop_color)
                lbl.image = img
            else:
                lbl = tk.Label(self.root, text="owo", bg=STATE.desktop_color,
                               fg="white",
                               font=("MS Sans Serif", 22, "bold"))
            x = random.randint(130, max(150, w - 120))
            y = random.randint(120, max(140, h - TASKBAR_H - 160))
            lbl.place(x=x, y=y)
            lbl.bind("<Button-1>", lambda e, l=lbl: self.show_fact(l))
            self.sprites.append(lbl)

    def clear(self):
        for s in self.sprites:
            try:
                s.destroy()
            except Exception:
                pass
        self.sprites = []

    def recolor(self, color):
        for s in self.sprites:
            try:
                s.configure(bg=color)
            except Exception:
                pass

    def show_fact(self, widget):
        SOUNDS.mascot()
        fact = random.choice(self.FACTS)
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        x = widget.winfo_x() + widget.winfo_width() + 8
        y = max(0, widget.winfo_y() - 20)
        popup.geometry(f"+{x}+{y}")
        popup.configure(bg="#c85fa0", bd=2, relief="raised")
        frame = tk.Frame(popup, bg="#fff0f5", bd=2, relief="sunken")
        frame.pack(padx=2, pady=2)
        tk.Label(frame, text="✧ anime fact ✧", bg="#fff0f5", fg="#c85fa0",
                 font=("MS Sans Serif", 8, "bold")).pack(pady=(6, 0))
        tk.Label(frame, text=fact, bg="#fff0f5", wraplength=200,
                 justify="left",
                 font=("MS Sans Serif", 8)).pack(padx=8, pady=6)
        tk.Button(frame, text="ok", font=("MS Sans Serif", 8),
                  bg="#ffd6e8", activebackground="#ffb3d9",
                  command=popup.destroy).pack(pady=(0, 6))