"""Settings window with tabbed panels."""
import tkinter as tk
from tkinter import colorchooser, filedialog

from core.state import STATE, persist_state, SFX_DIR
from core.sounds import SOUNDS, HAS_PYGAME
from core.retro_window import RetroWindow, rescale_fonts

try:
    from PIL import Image, ImageTk  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import platform


TABS = ["Appearance", "Desktop", "Mascots", "Sounds", "Account", "About"]


class SettingsWindow(RetroWindow):
    def __init__(self, master, desktop, initial_tab="Appearance"):
        super().__init__(master, title="Settings - 0W07",
                         width=520, height=460, x=200, y=80,
                         desktop=desktop)
        self.desktop = desktop
        self.tabs = {}
        self._current = None

        tab_bar = tk.Frame(self.content, bg="#c0c0c0")
        tab_bar.pack(fill="x")

        body = tk.Frame(self.content, bg="#c0c0c0")
        body.pack(fill="both", expand=True)

        for name in TABS:
            f = tk.Frame(body, bg="#c0c0c0")
            self.tabs[name] = f
            tk.Button(tab_bar, text=name, font=("MS Sans Serif", 8),
                      relief="raised", bg="#ffd6e8", fg="#7a2050", bd=2,
                      activebackground="#ffb3d9",
                      command=lambda n=name: self.show_tab(n)
                      ).pack(side="left", padx=1, pady=2)

        self._build_appearance(self.tabs["Appearance"])
        self._build_desktop(self.tabs["Desktop"])
        self._build_mascots(self.tabs["Mascots"])
        self._build_sounds(self.tabs["Sounds"])
        self._build_account(self.tabs["Account"])
        self._build_about(self.tabs["About"])

        self.show_tab(initial_tab)

    # ------------------------------------------------------------------
    def show_tab(self, name):
        if name not in self.tabs:
            name = "Appearance"
        for n, f in self.tabs.items():
            f.pack_forget()
        self.tabs[name].pack(fill="both", expand=True)
        self._current = name

    # ==================================================================
    #  Appearance
    # ==================================================================
    def _build_appearance(self, ap):
        tk.Label(ap, text="Text size", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")
                 ).pack(anchor="w", padx=10, pady=(10, 2))

        size_row = tk.Frame(ap, bg="#c0c0c0")
        size_row.pack(anchor="w", padx=10)
        scale_btns = {}

        def set_scale(new):
            old = STATE.text_scale
            if old == new:
                return
            rescale_fonts(self.desktop.root, new / old)
            STATE.text_scale = new
            for v, b in scale_btns.items():
                b.config(relief="sunken" if v == new else "raised")
            persist_state()

        for label, value in [("Small", 0.8), ("Normal", 1.0),
                             ("Large", 1.25), ("Huge", 1.5)]:
            b = tk.Button(size_row, text=label, font=("MS Sans Serif", 8),
                          width=8, bd=2,
                          command=lambda v=value: set_scale(v))
            b.pack(side="left", padx=2)
            b.config(relief="sunken" if value == STATE.text_scale else "raised")
            scale_btns[value] = b

        tk.Label(ap, text="Desktop colour", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")
                 ).pack(anchor="w", padx=10, pady=(16, 2))
        color_row = tk.Frame(ap, bg="#c0c0c0")
        color_row.pack(anchor="w", padx=10)

        def set_color(hexval):
            STATE.desktop_color = hexval
            STATE.wallpaper_path = None
            self.desktop.apply_wallpaper()
            self.desktop.root.configure(bg=hexval)
            self.desktop.mascots.recolor(hexval)
            self.desktop.recolor_icons(hexval)
            persist_state()

        for hexval in ["#008080", "#ffb3d9", "#c85fa0",
                       "#3a1a4d", "#1a1a2e", "#000000"]:
            tk.Button(color_row, bg=hexval, width=3, height=1, bd=2,
                      relief="raised",
                      command=lambda h=hexval: set_color(h)
                      ).pack(side="left", padx=2)

        def pick_custom():
            chosen = colorchooser.askcolor(color=STATE.desktop_color,
                                           title="Pick desktop colour")
            if chosen and chosen[1]:
                set_color(chosen[1])

        tk.Button(ap, text="Custom...", font=("MS Sans Serif", 8),
                  command=pick_custom).pack(anchor="w", padx=10, pady=(6, 0))

        def reset_all():
            old = STATE.text_scale
            if old != 1.0:
                rescale_fonts(self.desktop.root, 1.0 / old)
                STATE.text_scale = 1.0
            for v, b in scale_btns.items():
                b.config(relief="sunken" if v == 1.0 else "raised")
            set_color("#008080")
            STATE.show_clock = True
            STATE.mascots_enabled = False
            self.desktop.mascots.clear()
            STATE.skip_boot = False
            STATE.wallpaper_path = None
            self.desktop.apply_wallpaper()
            persist_state()

        tk.Button(ap, text="Reset to defaults", font=("MS Sans Serif", 8),
                  command=reset_all).pack(anchor="w", padx=10, pady=(24, 0))

    # ==================================================================
    #  Desktop
    # ==================================================================
    def _build_desktop(self, dt):
        tk.Label(dt, text="Taskbar", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")
                 ).pack(anchor="w", padx=10, pady=(10, 2))

        def toggle_clock():
            STATE.show_clock = not STATE.show_clock
            clock_btn.config(
                text=f"Clock: {'ON' if STATE.show_clock else 'OFF'}")
            persist_state()

        clock_btn = tk.Button(
            dt, font=("MS Sans Serif", 8),
            text=f"Clock: {'ON' if STATE.show_clock else 'OFF'}",
            command=toggle_clock)
        clock_btn.pack(anchor="w", padx=10)

        tk.Label(dt, text="Boot", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")
                 ).pack(anchor="w", padx=10, pady=(16, 2))

        def toggle_skip_boot():
            STATE.skip_boot = not STATE.skip_boot
            skip_btn.config(
                text=f"Skip boot screen: {'ON' if STATE.skip_boot else 'OFF'}")

        skip_btn = tk.Button(
            dt, font=("MS Sans Serif", 8),
            text=f"Skip boot screen: {'ON' if STATE.skip_boot else 'OFF'}",
            command=toggle_skip_boot)
        skip_btn.pack(anchor="w", padx=10)

        tk.Label(dt, text="Wallpaper", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")
                 ).pack(anchor="w", padx=10, pady=(16, 2))
        wall_row = tk.Frame(dt, bg="#c0c0c0")
        wall_row.pack(anchor="w", padx=10)

        def choose_wall():
            p = filedialog.askopenfilename(
                filetypes=[("Images", "*.png *.gif *.jpg *.jpeg"),
                           ("All", "*.*")])
            if p:
                STATE.wallpaper_path = p
                self.desktop.apply_wallpaper()
                persist_state()

        def clear_wall():
            STATE.wallpaper_path = None
            self.desktop.apply_wallpaper()
            self.desktop.root.configure(bg=STATE.desktop_color)
            self.desktop.mascots.recolor(STATE.desktop_color)
            self.desktop.recolor_icons(STATE.desktop_color)
            persist_state()

        tk.Button(wall_row, text="Choose image...",
                  font=("MS Sans Serif", 8),
                  command=choose_wall).pack(side="left", padx=(0, 4))
        tk.Button(wall_row, text="Clear", font=("MS Sans Serif", 8),
                  command=clear_wall).pack(side="left")

    # ==================================================================
    #  Mascots
    # ==================================================================
    def _build_mascots(self, mc):
        tk.Label(mc, text="Desktop mascots", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")
                 ).pack(anchor="w", padx=10, pady=(10, 2))
        tk.Label(mc, text="Click a mascot to hear a random anime fact.",
                 bg="#c0c0c0", font=("MS Sans Serif", 8),
                 wraplength=460, justify="left"
                 ).pack(anchor="w", padx=10)

        def refresh_mascot_btn():
            mascot_btn.config(
                text=f"Mascots: {'ON' if STATE.mascots_enabled else 'OFF'}")

        def toggle_mascots():
            STATE.mascots_enabled = not STATE.mascots_enabled
            if STATE.mascots_enabled:
                self.desktop.mascots.spawn(STATE.mascot_count)
            else:
                self.desktop.mascots.clear()
            refresh_mascot_btn()
            persist_state()

        mascot_btn = tk.Button(
            mc, font=("MS Sans Serif", 8),
            text=f"Mascots: {'ON' if STATE.mascots_enabled else 'OFF'}",
            command=toggle_mascots)
        mascot_btn.pack(anchor="w", padx=10, pady=(6, 0))

        tk.Label(mc, text="How many?", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)
                 ).pack(anchor="w", padx=10, pady=(10, 0))
        count_row = tk.Frame(mc, bg="#c0c0c0")
        count_row.pack(anchor="w", padx=10)
        count_btns = {}

        def set_count(n):
            STATE.mascot_count = n
            for v, b in count_btns.items():
                b.config(relief="sunken" if v == n else "raised")
            if STATE.mascots_enabled:
                self.desktop.mascots.spawn(n)
            persist_state()

        for n in [1, 2, 3, 5]:
            b = tk.Button(count_row, text=str(n), width=3,
                          font=("MS Sans Serif", 8),
                          relief="sunken" if n == STATE.mascot_count else "raised",
                          command=lambda v=n: set_count(v))
            b.pack(side="left", padx=2)
            count_btns[n] = b

    # ==================================================================
    #  Sounds
    # ==================================================================
    def _build_sounds(self, sn):
        tk.Label(sn, text="Sound", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")
                 ).pack(anchor="w", padx=10, pady=(10, 2))
        tk.Label(sn,
                 text=("Drop sound files into assets/music/sfx/\n"
                       "named: startup, click, mascot, error, shutdown."),
                 bg="#c0c0c0", font=("MS Sans Serif", 7), justify="left"
                 ).pack(anchor="w", padx=10)
        tk.Label(sn, text=f"Folder: {SFX_DIR}", bg="#c0c0c0",
                 font=("MS Sans Serif", 7), justify="left"
                 ).pack(anchor="w", padx=10, pady=(0, 8))

        def make_toggle(parent, label, attr, test_fn=None):
            row = tk.Frame(parent, bg="#c0c0c0")
            row.pack(anchor="w", padx=10, pady=2, fill="x")

            def flip():
                setattr(STATE, attr, not getattr(STATE, attr))
                btn.config(
                    text=f"{label}: "
                         f"{'ON' if getattr(STATE, attr) else 'OFF'}")

            btn = tk.Button(
                row, font=("MS Sans Serif", 8), width=18,
                text=f"{label}: {'ON' if getattr(STATE, attr) else 'OFF'}",
                command=flip)
            btn.pack(side="left")
            if test_fn:
                tk.Button(row, text="Test", font=("MS Sans Serif", 8),
                          command=test_fn).pack(side="left", padx=4)

        make_toggle(sn, "Master sound",  "sound_enabled",  SOUNDS.startup)
        make_toggle(sn, "Startup chime", "startup_sound",  SOUNDS.startup)
        make_toggle(sn, "Click sounds",  "click_sounds",   SOUNDS.click)
        make_toggle(sn, "Mascot sound",  "mascot_sounds",  SOUNDS.mascot)
        make_toggle(sn, "Error sound",   "error_sounds",   SOUNDS.error)

    # ==================================================================
    #  Account
    # ==================================================================
    def _build_account(self, ac):
        tk.Label(ac, text="Account", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")
                 ).pack(anchor="w", padx=10, pady=(10, 2))
        tk.Label(ac, text="Username", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)
                 ).pack(anchor="w", padx=10)
        name_var = tk.StringVar(value=STATE.username)
        name_entry = tk.Entry(ac, textvariable=name_var,
                              font=("MS Sans Serif", 10),
                              bg="#fff8fc", fg="#7a2050",
                              relief="sunken", bd=2, width=24)
        name_entry.pack(anchor="w", padx=10, pady=(2, 6))

        def save_name():
            STATE.username = name_var.get().strip() or "owlito"
            persist_state()
            SOUNDS.click()

        tk.Button(ac, text="Save", font=("MS Sans Serif", 8),
                  command=save_name).pack(anchor="w", padx=10)

    # ==================================================================
    #  About
    # ==================================================================
    def _build_about(self, ab):
        tk.Label(ab, text="0W07", bg="#c0c0c0", fg="#c85fa0",
                 font=("MS Sans Serif", 18, "bold")).pack(pady=(20, 0))
        tk.Label(ab, text="by owlito", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack()
        tk.Label(ab, text="est. 2007", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack()
        tk.Label(ab,
                 text="A retro Windows desktop built in Python + Tkinter.",
                 bg="#c0c0c0", font=("MS Sans Serif", 8)
                 ).pack(pady=(16, 0))
        tk.Label(ab,
                 text=f"Python {platform.python_version()}  |  "
                      f"{platform.system()} {platform.release()}",
                 bg="#c0c0c0", font=("MS Sans Serif", 7)
                 ).pack(pady=(4, 0))
        tk.Label(ab,
                 text=f"Pillow: "
                      f"{'installed' if HAS_PIL else 'not installed'}",
                 bg="#c0c0c0", font=("MS Sans Serif", 7)).pack()
        tk.Label(ab,
                 text=f"pygame: "
                      f"{'installed' if HAS_PYGAME else 'not installed'}",
                 bg="#c0c0c0", font=("MS Sans Serif", 7)).pack()
        tk.Label(ab, text=f"Installed apps: {len(STATE.installed_apps)}",
                 bg="#c0c0c0", font=("MS Sans Serif", 7)).pack()