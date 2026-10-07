import tkinter as tk
import time, random, os, winsound, platform, sys, traceback, json
from tkinter import colorchooser, filedialog, messagebox

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    HAS_PYGAME = True
except Exception as _pg_err:
    HAS_PYGAME = False
    print("pygame not available:", _pg_err)


def _tk_exception_handler(exc, val, tb):
    print("\n!!! Tkinter callback crashed !!!", file=sys.stderr)
    traceback.print_exception(exc, val, tb, file=sys.stderr)

def _excepthook(exc, val, tb):
    print("\n!!! Uncaught exception !!!", file=sys.stderr)
    traceback.print_exception(exc, val, tb, file=sys.stderr)

sys.excepthook = _excepthook


# ============================================================
#  PATHS
# ============================================================
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
MASCOTS_DIR = os.path.join(ASSETS_DIR, "mascots")
SOUNDS_DIR  = os.path.join(ASSETS_DIR, "sounds")
WALLS_DIR   = os.path.join(ASSETS_DIR, "wallpapers")
MUSIC_DIR   = os.path.join(ASSETS_DIR, "music")
SFX_DIR     = os.path.join(MUSIC_DIR, "sfx")
CONFIG_PATH = os.path.join(ASSETS_DIR, "config.json")

TASKBAR_H = 32


# ============================================================
#  CONFIG PERSISTENCE
# ============================================================
def load_config():
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception as e:
            print("config load failed:", e)
    return {}

def save_config(data):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("config save failed:", e)


# ============================================================
#  GLOBAL STATE
# ============================================================
class OW07State:
    def __init__(self):
        self.text_scale = 1.0
        self.desktop_color = "#008080"
        self.mascots_enabled = False
        self.mascot_count = 3
        self.show_clock = True
        self.sound_enabled = True
        self.startup_sound = True
        self.click_sounds = False
        self.mascot_sounds = True
        self.error_sounds = True
        self.skip_boot = False
        self.wallpaper_path = None
        self.installed_apps = set()
        self.username = "owlito"

STATE = OW07State()

# Load saved config
_cfg = load_config()
STATE.text_scale = _cfg.get("text_scale", 1.0)
STATE.desktop_color = _cfg.get("desktop_color", "#008080")
STATE.mascots_enabled = _cfg.get("mascots_enabled", False)
STATE.mascot_count = _cfg.get("mascot_count", 3)
STATE.show_clock = _cfg.get("show_clock", True)
STATE.wallpaper_path = _cfg.get("wallpaper_path")
STATE.installed_apps = set(_cfg.get("installed_apps", []))
STATE.username = _cfg.get("username", "owlito")


def persist_state():
    save_config({
        "text_scale": STATE.text_scale,
        "desktop_color": STATE.desktop_color,
        "mascots_enabled": STATE.mascots_enabled,
        "mascot_count": STATE.mascot_count,
        "show_clock": STATE.show_clock,
        "wallpaper_path": STATE.wallpaper_path,
        "installed_apps": sorted(STATE.installed_apps),
        "username": STATE.username,
    })


# ============================================================
#  SOUND
# ============================================================
class SoundManager:
    SFX_EXTS = (".wav", ".mp3", ".ogg", ".flac")

    def __init__(self):
        self._cache = {}

    def _find_path(self, name):
        if os.path.isdir(SFX_DIR):
            for ext in self.SFX_EXTS:
                p = os.path.join(SFX_DIR, name + ext)
                if os.path.isfile(p): return p
        p = os.path.join(SOUNDS_DIR, name + ".wav")
        if os.path.isfile(p): return p
        return None

    def _play(self, name, beep_kind):
        path = self._find_path(name)
        if not path:
            try: winsound.MessageBeep(beep_kind)
            except Exception: pass
            return
        ext = path.lower().rsplit(".", 1)[-1]
        if ext == "wav" and not HAS_PYGAME:
            try:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            except Exception as e:
                print("winsound failed:", name, e)
        if HAS_PYGAME:
            try:
                snd = self._cache.get(name)
                if snd is None or getattr(snd, "_src_path", None) != path:
                    snd = pygame.mixer.Sound(path)
                    snd._src_path = path
                    self._cache[name] = snd
                snd.stop(); snd.play()
                return
            except Exception as e:
                print("pygame sfx failed:", name, e)
        try: winsound.MessageBeep(beep_kind)
        except Exception: pass

    def startup(self):
        if not (STATE.sound_enabled and STATE.startup_sound): return
        self._play("startup", winsound.MB_ICONASTERISK)
    def click(self):
        if not (STATE.sound_enabled and STATE.click_sounds): return
        self._play("click", winsound.MB_OK)
    def mascot(self):
        if not (STATE.sound_enabled and STATE.mascot_sounds): return
        self._play("mascot", winsound.MB_ICONASTERISK)
    def error(self):
        if not (STATE.sound_enabled and STATE.error_sounds): return
        self._play("error", winsound.MB_ICONHAND)
    def shutdown(self):
        if not STATE.sound_enabled: return
        self._play("shutdown", winsound.MB_ICONEXCLAMATION)

SOUNDS = SoundManager()


# ============================================================
#  FONT RESCALING
# ============================================================
def rescale_fonts(widget, ratio):
    try:
        f = widget.cget("font")
        if isinstance(f, (tuple, list)) and len(f) >= 2 and isinstance(f[1], int):
            fam, size = f[0], f[1]
            new_size = max(6, int(round(size * ratio)))
            widget.config(font=(fam, new_size) + tuple(f[2:]))
    except Exception: pass
    for child in widget.winfo_children():
        rescale_fonts(child, ratio)


# ============================================================
#  LOGIN SCREEN
# ============================================================
class LoginScreen:
    def __init__(self, root, on_login, on_shutdown):
        self.root = root
        self.on_login = on_login
        self.on_shutdown = on_shutdown

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.configure(bg="#ffd6e8")

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{sw}x{sh}+0+0")

        try: self.win.attributes("-topmost", True)
        except Exception: pass
        try: self.win.deiconify()
        except Exception: pass
        try: self.win.lift()
        except Exception: pass

        # Center column
        col = tk.Frame(self.win, bg="#ffd6e8")
        col.place(relx=0.5, rely=0.5, anchor="center")

        # Header
        tk.Label(col, text="♥ 0W07 ♥", bg="#ffd6e8", fg="#c85fa0",
                 font=("MS Sans Serif", 42, "bold")).pack(pady=(0, 4))
        tk.Label(col, text="welcome back, owlito", bg="#ffd6e8", fg="#a04878",
                 font=("MS Sans Serif", 10)).pack(pady=(0, 24))

        # Avatar
        avatar_frame = tk.Frame(col, bg="#ffd6e8")
        avatar_frame.pack(pady=(0, 24))
        cv = tk.Canvas(avatar_frame, width=120, height=120,
                       bg="#ffd6e8", highlightthickness=0)
        cv.pack()
        cv.create_oval(4, 4, 116, 116, fill="#ffb3d9", outline="#c85fa0", width=3)
        cv.create_text(60, 60, text="🦉", font=("Segoe UI Emoji", 52))

        tk.Label(col, text=STATE.username, bg="#ffd6e8", fg="#7a2050",
                 font=("MS Sans Serif", 14, "bold")).pack()

        # Password field
        pw_frame = tk.Frame(col, bg="#ffd6e8")
        pw_frame.pack(pady=20)
        tk.Label(pw_frame, text="Password", bg="#ffd6e8", fg="#7a2050",
                 font=("MS Sans Serif", 9)).pack(anchor="w")
        self.pw_var = tk.StringVar()
        self.pw_entry = tk.Entry(pw_frame, textvariable=self.pw_var, show="●",
                                  width=26, font=("MS Sans Serif", 11),
                                  bg="#fff8fc", fg="#7a2050",
                                  insertbackground="#c85fa0",
                                  relief="sunken", bd=2, justify="center")
        self.pw_entry.pack(pady=(4, 0), ipady=4)
        self.pw_entry.focus_set()
        self.pw_entry.bind("<Return>", lambda e: self.try_login())

        # Buttons
        btn_row = tk.Frame(col, bg="#ffd6e8")
        btn_row.pack(pady=(20, 0))

        tk.Button(btn_row, text="Log In", width=12,
                  font=("MS Sans Serif", 10, "bold"),
                  bg="#ffb3d9", fg="#7a2050", relief="raised", bd=2,
                  activebackground="#ff69b4",
                  command=self.try_login).pack(side="left", padx=4)

        tk.Button(btn_row, text="Shut Down", width=12,
                  font=("MS Sans Serif", 10),
                  bg="#ffd6e8", fg="#7a2050", relief="raised", bd=2,
                  activebackground="#ffb3d9",
                  command=self.shutdown).pack(side="left", padx=4)

        self.hint = tk.Label(col, text="(any password works — or leave it blank)",
                              bg="#ffd6e8", fg="#c894b3",
                              font=("MS Sans Serif", 8))
        self.hint.pack(pady=(16, 0))

        self.win.after(150, self._focus)

    def _focus(self):
        try: self.pw_entry.focus_force()
        except Exception: pass

    def try_login(self):
        SOUNDS.click()
        STATE.username = STATE.username or "owlito"
        try: self.win.destroy()
        except Exception: pass
        self.on_login()

    def shutdown(self):
        try: self.win.destroy()
        except Exception: pass
        self.on_shutdown()


# ============================================================
#  BOOT SCREEN
# ============================================================
class BootScreen:
    def __init__(self, root, on_done):
        self.root = root
        self.on_done = on_done
        self.finished = False

        self.splash = tk.Toplevel(root)
        self.splash.overrideredirect(True)
        self.splash.configure(bg="#000000")
        sw = self.splash.winfo_screenwidth()
        sh = self.splash.winfo_screenheight()
        self.splash.geometry(f"{sw}x{sh}+0+0")
        try: self.splash.deiconify()
        except Exception: pass
        try: self.splash.lift()
        except Exception: pass
        try: self.splash.attributes("-topmost", True)
        except Exception: pass
        try: self.splash.after(120, self._grab_focus)
        except Exception: pass
        try: SOUNDS.startup()
        except Exception as e: print("[boot] startup sound failed:", e)

        container = tk.Frame(self.splash, bg="#000000")
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text="0W07", bg="#000000", fg="#ffb3d9",
                 font=("MS Sans Serif", 72, "bold")).pack()
        tk.Label(container, text="version 0.6   |   owlito   |   est. 2007",
                 bg="#000000", fg="#008080",
                 font=("MS Sans Serif", 10)).pack(pady=(0, 24))

        self._image_ref = None
        try:
            img = self._load_boot_image()
            if img is not None:
                self._image_ref = img
                tk.Label(container, image=img, bg="#000000").pack(pady=(0, 24))
        except Exception as e: print("[boot] image failed:", e)

        bar_wrap = tk.Frame(container, bg="#000000")
        bar_wrap.pack()
        self.bar_bg = tk.Frame(bar_wrap, bg="#2a2a2a", width=420, height=20,
                               relief="sunken", bd=2)
        self.bar_bg.pack(); self.bar_bg.pack_propagate(False)
        self.bar_fill = tk.Frame(self.bar_bg, bg="#ff69b4")
        self.bar_fill.place(x=0, y=0, width=0, height=16)

        self.status = tk.Label(container, text="Starting 0W07...",
                               bg="#000000", fg="#ffb3d9",
                               font=("MS Sans Serif", 8))
        self.status.pack(pady=(8, 0))
        tk.Label(container, text="press ESC to skip", bg="#000000",
                 fg="#804060", font=("MS Sans Serif", 7)).pack(pady=(16, 0))

        self.steps = 70; self.current = 0; self.bar_target = 416
        self.messages = [
            (0.00, "Starting 0W07..."), (0.15, "Loading kernel..."),
            (0.35, "Mounting file system..."), (0.55, "Loading apps..."),
            (0.75, "Waking up the desktop..."), (0.90, "Almost there..."),
        ]
        self.splash.bind("<Escape>", lambda e: self.finish())
        self.splash.bind("<Return>", lambda e: self.finish())
        self.splash.after(100, self._tick)

    def _grab_focus(self):
        try: self.splash.focus_force()
        except Exception: pass

    def _load_boot_image(self):
        for name in ["boot.png", "boot.gif", "boot.jpg", "boot.jpeg",
                     "startup.png", "startup.gif"]:
            path = os.path.join(ASSETS_DIR, name)
            if not os.path.isfile(path): continue
            ext = name.lower().rsplit(".", 1)[-1]
            if ext in ("jpg", "jpeg"):
                if HAS_PIL:
                    try:
                        img = Image.open(path); img.thumbnail((360, 360))
                        return ImageTk.PhotoImage(img)
                    except Exception as e: print("[boot] bad image:", e)
            else:
                try: return tk.PhotoImage(file=path)
                except Exception as e: print("[boot] bad image:", e)
        return None

    def _tick(self):
        if self.finished: return
        if self.current >= self.steps:
            try: self.status.config(text="Welcome.")
            except Exception: pass
            self.splash.after(400, self.finish); return
        self.current += 1
        pct = self.current / self.steps
        try:
            self.bar_fill.place(x=0, y=0, width=int(self.bar_target * pct), height=16)
            for t, m in reversed(self.messages):
                if pct >= t: self.status.config(text=m); break
        except Exception as e: print("[boot] tick failed:", e)
        self.splash.after(50, self._tick)

    def finish(self):
        if self.finished: return
        self.finished = True
        try: self.splash.destroy()
        except Exception: pass
        try: self.on_done()
        except Exception as e:
            print("[boot] handoff failed:", e); traceback.print_exc()
            try: self.root.deiconify()
            except Exception: pass


# ============================================================
#  SHUTDOWN SCREEN
# ============================================================
class ShutdownScreen:
    def __init__(self, root):
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.configure(bg="#000000")
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{sw}x{sh}+0+0")
        try: self.win.attributes("-topmost", True)
        except Exception: pass
        try: self.win.deiconify()
        except Exception: pass
        try: self.win.lift()
        except Exception: pass

        try: root.withdraw()
        except Exception: pass
        for w in list(root.winfo_children()):
            if isinstance(w, tk.Toplevel):
                try: w.destroy()
                except Exception: pass

        col = tk.Frame(self.win, bg="#000000")
        col.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(col, text="It is now safe to turn off\nyour computer.",
                 bg="#000000", fg="#ff8c00",
                 font=("MS Sans Serif", 28, "bold"),
                 justify="center").pack(pady=(0, 40))

        btn_row = tk.Frame(col, bg="#000000")
        btn_row.pack()

        tk.Button(btn_row, text="Restart 0W07", width=16,
                  font=("MS Sans Serif", 10, "bold"),
                  bg="#c0c0c0", fg="#000000", relief="raised", bd=2,
                  command=self.restart).pack(side="left", padx=8)

        tk.Button(btn_row, text="Turn Off", width=16,
                  font=("MS Sans Serif", 10),
                  bg="#c0c0c0", fg="#000000", relief="raised", bd=2,
                  command=self.turn_off).pack(side="left", padx=8)

        tk.Label(col, text="(Restart relaunches 0W07 — Turn Off closes it)",
                 bg="#000000", fg="#444444",
                 font=("MS Sans Serif", 8)).pack(pady=(24, 0))

    def restart(self):
        try: self.win.destroy()
        except Exception: pass
        try: self.root.destroy()
        except Exception: pass
        time.sleep(0.2)
        os.execl(sys.executable, sys.executable, *sys.argv)

    def turn_off(self):
        try: self.root.destroy()
        except Exception: pass


# ============================================================
#  RETRO WINDOW
# ============================================================
class RetroWindow(tk.Toplevel):
    def __init__(self, master, title="Window", width=300, height=200,
                 x=120, y=120, on_close=None, desktop=None, resizable=True):
        super().__init__(master)
        self.overrideredirect(True)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.configure(bg="#c0c0c0")
        self.on_close = on_close
        self.desktop = desktop
        self.minimized = False
        self.maximized = False
        self._prev_geo = None
        self.taskbar_btn = None

        self.title_bar = tk.Frame(self, bg="#c85fa0", relief="raised", bd=2)
        self.title_bar.pack(fill="x")
        self.title_label = tk.Label(self.title_bar, text=title, bg="#c85fa0",
                                    fg="white", font=("MS Sans Serif", 8, "bold"))
        self.title_label.pack(side="left", padx=5)

        self.close_btn = tk.Button(self.title_bar, text="X", bg="#ffd6e8",
                                   fg="#7a2050", relief="raised", bd=1,
                                   command=self._close, activebackground="#ffb3d9",
                                   font=("MS Sans Serif", 8, "bold"), width=2)
        self.close_btn.pack(side="right", padx=1, pady=1)
        self.max_btn = tk.Button(self.title_bar, text="□", bg="#ffd6e8",
                                 fg="#7a2050", relief="raised", bd=1,
                                 command=self.toggle_maximize,
                                 activebackground="#ffb3d9",
                                 font=("MS Sans Serif", 8, "bold"), width=2)
        self.max_btn.pack(side="right", padx=1, pady=1)
        self.min_btn = tk.Button(self.title_bar, text="_", bg="#ffd6e8",
                                 fg="#7a2050", relief="raised", bd=1,
                                 command=self.minimize, activebackground="#ffb3d9",
                                 font=("MS Sans Serif", 8, "bold"), width=2)
        self.min_btn.pack(side="right", padx=1, pady=1)

        self.content = tk.Frame(self, bg="#c0c0c0", relief="sunken", bd=2)
        self.content.pack(fill="both", expand=True, padx=2, pady=2)

        for w in (self.title_bar, self.title_label):
            w.bind("<Button-1>", self.start_move)
            w.bind("<B1-Motion>", self.do_move)
            w.bind("<Double-Button-1>", lambda e: self.toggle_maximize())
        self.bind("<Button-1>", lambda e: self._focus(), add="+")

        if desktop:
            desktop.register_window(self, title)

    def set_title(self, text):
        try: self.title_label.config(text=text)
        except Exception: pass
        if self.taskbar_btn:
            try: self.taskbar_btn.config(text=OW07Desktop._short(text))
            except Exception: pass

    def _focus(self):
        try:
            self.lift()
            if self.desktop: self.desktop.highlight_taskbar(self)
        except Exception: pass

    def start_move(self, event):
        if self.maximized: return
        self._dx, self._dy = event.x, event.y

    def do_move(self, event):
        if self.maximized: return
        self.geometry(f"+{self.winfo_x() + event.x - self._dx}+{self.winfo_y() + event.y - self._dy}")

    def minimize(self):
        self.minimized = True
        self.withdraw()
        if self.desktop: self.desktop.set_taskbar_state(self, minimized=True)

    def restore(self):
        self.minimized = False
        self.deiconify(); self.lift(); self._focus()
        if self.desktop: self.desktop.set_taskbar_state(self, minimized=False)

    def toggle_maximize(self):
        if not self.winfo_exists(): return
        if self.maximized:
            if self._prev_geo: self.geometry(self._prev_geo)
            self.maximized = False; self.max_btn.config(text="□")
        else:
            self._prev_geo = self.geometry()
            sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
            self.geometry(f"{sw}x{sh - TASKBAR_H}+0+0")
            self.maximized = True; self.max_btn.config(text="❐")

    def _close(self):
        if self.on_close:
            try: self.on_close()
            except Exception: pass
        if self.desktop:
            try: self.desktop.unregister_window(self)
            except Exception: pass
        self.destroy()


# ============================================================
#  MASCOT MANAGER
# ============================================================
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
                        self.images.append(tk.PhotoImage(file=os.path.join(MASCOTS_DIR, name)))
                    except Exception as e: print("bad mascot image", name, e)

    def spawn(self, count=3):
        self.clear()
        w = max(self.root.winfo_width(), 800)
        h = max(self.root.winfo_height(), 600)
        for _ in range(count):
            if self.images:
                img = random.choice(self.images)
                lbl = tk.Label(self.root, image=img, bd=0, bg=STATE.desktop_color)
                lbl.image = img
            else:
                lbl = tk.Label(self.root, text="owo", bg=STATE.desktop_color,
                               fg="white", font=("MS Sans Serif", 22, "bold"))
            x = random.randint(130, max(150, w - 120))
            y = random.randint(120, max(140, h - TASKBAR_H - 160))
            lbl.place(x=x, y=y)
            lbl.bind("<Button-1>", lambda e, l=lbl: self.show_fact(l))
            self.sprites.append(lbl)

    def clear(self):
        for s in self.sprites:
            try: s.destroy()
            except Exception: pass
        self.sprites = []

    def recolor(self, color):
        for s in self.sprites:
            try: s.configure(bg=color)
            except Exception: pass

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
                 justify="left", font=("MS Sans Serif", 8)).pack(padx=8, pady=6)
        tk.Button(frame, text="ok", font=("MS Sans Serif", 8),
                  bg="#ffd6e8", activebackground="#ffb3d9",
                  command=popup.destroy).pack(pady=(0, 6))


# ============================================================
#  FAKE FILESYSTEM
# ============================================================
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


# ============================================================
#  STORE CATALOG
# ============================================================
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
        if a["id"] == app_id: return a
    return None


# ============================================================
#  TETRIS
# ============================================================
class TetrisWindow(RetroWindow):
    COLS, ROWS, CELL = 10, 20, 22
    SHAPES = {
        "I": ([(0,0),(1,0),(2,0),(3,0)], "#00f0f0"),
        "O": ([(0,0),(1,0),(0,1),(1,1)], "#f0f000"),
        "T": ([(0,0),(1,0),(2,0),(1,1)], "#a000f0"),
        "S": ([(1,0),(2,0),(0,1),(1,1)], "#00f000"),
        "Z": ([(0,0),(1,0),(1,1),(2,1)], "#f00000"),
        "J": ([(0,0),(0,1),(1,1),(2,1)], "#0000f0"),
        "L": ([(2,0),(0,1),(1,1),(2,1)], "#f0a000"),
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
            try: self.after_cancel(self._job)
            except Exception: pass
            self._job = None
        self.grid = [[None]*self.COLS for _ in range(self.ROWS)]
        self.score = 0; self.lines = 0; self.game_over = False
        self.score_lbl.config(text="0"); self.lines_lbl.config(text="0")
        self.current = None; self.next_piece = self.random_piece()
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
            if gx < 0 or gx >= self.COLS or gy >= self.ROWS: return True
            if gy >= 0 and self.grid[gy][gx] is not None: return True
        return False

    def on_key(self, event):
        if self.game_over or not self.current: return
        k = event.keysym.lower()
        if k == "left":
            if not self.collides(self.current["coords"], self.current["x"] - 1, self.current["y"]):
                self.current["x"] -= 1; self.draw()
        elif k == "right":
            if not self.collides(self.current["coords"], self.current["x"] + 1, self.current["y"]):
                self.current["x"] += 1; self.draw()
        elif k == "down":
            if not self.collides(self.current["coords"], self.current["x"], self.current["y"] + 1):
                self.current["y"] += 1; self.draw()
        elif k == "up":
            # rotate
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
        if self.game_over: return
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
        # clear lines
        new_grid = [r for r in self.grid if any(c is None for c in r)]
        cleared = self.ROWS - len(new_grid)
        for _ in range(cleared):
            new_grid.insert(0, [None]*self.COLS)
        self.grid = new_grid
        if cleared:
            self.lines += cleared
            self.score += cleared * 100
            self.score_lbl.config(text=str(self.score))
            self.lines_lbl.config(text=str(self.lines))
        self.spawn_piece()

    def draw(self):
        c = self.canvas; C = self.CELL
        c.delete("all")
        for y in range(self.ROWS):
            for x in range(self.COLS):
                if self.grid[y][x]:
                    c.create_rectangle(x*C+1, y*C+1, (x+1)*C-1, (y+1)*C-1,
                                       fill=self.grid[y][x], outline="#0a000a")
        if self.current and not self.game_over:
            for (x, y) in self.current["coords"]:
                gx, gy = self.current["x"] + x, self.current["y"] + y
                if gy >= 0:
                    c.create_rectangle(gx*C+1, gy*C+1, (gx+1)*C-1, (gy+1)*C-1,
                                       fill=self.current["color"], outline="#0a000a")
        # next preview
        self.next_canvas.delete("all")
        if self.next_piece:
            NC = 18
            for (x, y) in self.next_piece["coords"]:
                self.next_canvas.create_rectangle(x*NC+10, y*NC+20,
                                                   (x+1)*NC+8, (y+1)*NC+18,
                                                   fill=self.next_piece["color"],
                                                   outline="#0a000a")
        if self.game_over:
            c.create_rectangle(0, self.ROWS*C//2 - 30, self.COLS*C, self.ROWS*C//2 + 30,
                               fill="#1a0a1a", outline="#ff69b4", width=2)
            c.create_text(self.COLS*C//2, self.ROWS*C//2 - 8, text="GAME OVER",
                          fill="#ff69b4", font=("MS Sans Serif", 16, "bold"))
            c.create_text(self.COLS*C//2, self.ROWS*C//2 + 14,
                          text=f"Score: {self.score}", fill="white",
                          font=("MS Sans Serif", 9))

    def _close(self):
        if self._job:
            try: self.after_cancel(self._job)
            except Exception: pass
            self._job = None
        super()._close()


# ============================================================
#  CLOCK
# ============================================================
class ClockWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="Clock", width=280, height=320,
                         desktop=desktop)
        self.canvas = tk.Canvas(self.content, width=240, height=240,
                                bg="#fff0f5", highlightthickness=0, bd=0)
        self.canvas.pack(pady=10)
        self.date_lbl = tk.Label(self.content, text="", bg="#c0c0c0",
                                 fg="#7a2050", font=("MS Sans Serif", 9, "bold"))
        self.date_lbl.pack(pady=(0, 8))
        self._job = None
        self.tick()

    def tick(self):
        if not self.winfo_exists(): return
        c = self.canvas; c.delete("all")
        cx, cy, r = 120, 120, 100
        c.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#ffd6e8", outline="#c85fa0", width=3)
        c.create_oval(cx-r+8, cy-r+8, cx+r-8, cy+r-8, fill="#fff8fc", outline="")
        # tick marks
        for i in range(12):
            ang = i * 30 * 3.14159 / 180
            x1 = cx + (r-18) * __import__("math").sin(ang)
            y1 = cy - (r-18) * __import__("math").cos(ang)
            x2 = cx + (r-8) * __import__("math").sin(ang)
            y2 = cy - (r-8) * __import__("math").cos(ang)
            c.create_line(x1, y1, x2, y2, fill="#c85fa0", width=2)
        # hands
        import math
        t = time.localtime()
        h, m, s = t.tm_hour % 12, t.tm_min, t.tm_sec
        for ang_deg, length, width, color in [
            ((h + m/60) * 30, 50, 6, "#7a2050"),
            ((m + s/60) * 6, 70, 4, "#c85fa0"),
            (s * 6, 80, 2, "#ff69b4"),
        ]:
            ang = ang_deg * math.pi / 180
            x2 = cx + length * math.sin(ang)
            y2 = cy - length * math.cos(ang)
            c.create_line(cx, cy, x2, y2, fill=color, width=width, capstyle="round")
        c.create_oval(cx-6, cy-6, cx+6, cy+6, fill="#c85fa0", outline="")
        self.date_lbl.config(text=time.strftime("%A, %B %d, %Y"))
        self._job = self.after(1000, self.tick)

    def _close(self):
        if self._job:
            try: self.after_cancel(self._job)
            except Exception: pass
            self._job = None
        super()._close()


# ============================================================
#  DICE ROLLER
# ============================================================
class DiceWindow(RetroWindow):
    FACE = {1:"⚀", 2:"⚁", 3:"⚂", 4:"⚃", 5:"⚄", 6:"⚅"}

    def __init__(self, master, desktop):
        super().__init__(master, title="Dice Roller", width=320, height=260,
                         desktop=desktop)
        tk.Label(self.content, text="🎲 Dice Roller 🎲", bg="#c0c0c0",
                 fg="#c85fa0", font=("MS Sans Serif", 12, "bold")).pack(pady=(12, 4))

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
        self.total_lbl.config(text=f"Total: {sum(rolls)}   ({', '.join(map(str, rolls))})")


# ============================================================
#  STORE WINDOW
# ============================================================
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

        # Category sidebar
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

        # Right pane
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
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.status = tk.Label(self.content, text="", bg="#c0c0c0", fg="#7a2050",
                                font=("MS Sans Serif", 8), anchor="w")
        self.status.pack(fill="x", padx=6, pady=(0, 4))

        self.refresh()

    def current_category(self):
        sel = self.cat_list.curselection()
        if not sel: return "All"
        return self.categories[sel[0]]

    def refresh(self):
        for w in self.inner.winfo_children():
            w.destroy()

        cat = self.current_category()
        for app in STORE_APPS:
            if cat != "All" and app["category"] != cat: continue
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
        cv.create_text(26, 26, text=app["icon"], font=("Segoe UI Emoji", 20))

        mid = tk.Frame(card, bg="white")
        mid.pack(side="left", fill="both", expand=True, padx=4, pady=8)
        tk.Label(mid, text=app["name"], bg="white", fg="#7a2050",
                 font=("MS Sans Serif", 10, "bold"), anchor="w").pack(fill="x")
        tk.Label(mid, text=app["description"], bg="white", fg="#555555",
                 font=("MS Sans Serif", 8), anchor="w",
                 wraplength=280, justify="left").pack(fill="x")
        tk.Label(mid, text=f"{app['category']}  ·  {app['size']}",
                 bg="white", fg="#a04878",
                 font=("MS Sans Serif", 7), anchor="w").pack(fill="x", pady=(2, 0))

        right = tk.Frame(card, bg="white")
        right.pack(side="right", padx=8)

        installed = app["id"] in STATE.installed_apps

        if installed:
            tk.Button(right, text="Play", width=10,
                      font=("MS Sans Serif", 9, "bold"),
                      bg="#ffb3d9", fg="#7a2050",
                      activebackground="#ff69b4",
                      command=lambda a=app: self.launch(a)).pack(pady=2)
            tk.Button(right, text="Uninstall", width=10,
                      font=("MS Sans Serif", 8),
                      bg="#ffd6e8", fg="#7a2050",
                      activebackground="#ffb3d9",
                      command=lambda a=app: self.uninstall(a)).pack(pady=2)
        else:
            tk.Button(right, text="Install", width=10,
                      font=("MS Sans Serif", 9, "bold"),
                      bg="#c8f5c8", fg="#2a5a2a",
                      activebackground="#a0e0a0",
                      command=lambda a=app: self.install(a)).pack(pady=2)

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


# ============================================================
#  MUSIC PLAYER (unchanged from last version)
# ============================================================
class MusicPlayerWindow(RetroWindow):
    AUDIO_EXTS = (".mp3", ".ogg", ".wav", ".flac")
    EXCLUDED_FOLDERS = {"sfx"}

    def __init__(self, master, desktop):
        super().__init__(master, title="0W07 Music Player",
                         width=520, height=600, desktop=desktop)
        header = tk.Frame(self.content, bg="#fff0f5")
        header.pack(fill="x")
        tk.Label(header, text="♪ 0W07 Music ♪", bg="#fff0f5", fg="#c85fa0",
                 font=("MS Sans Serif", 12, "bold")).pack(pady=4)
        self.now_playing = tk.Label(self.content, text="No track loaded",
                                     bg="#c85fa0", fg="white", anchor="w",
                                     padx=8, pady=6,
                                     font=("MS Sans Serif", 9, "bold"))
        self.now_playing.pack(fill="x")
        prog_frame = tk.Frame(self.content, bg="#c0c0c0")
        prog_frame.pack(fill="x", padx=6, pady=(8, 2))
        self.progress_canvas = tk.Canvas(prog_frame, height=14, bg="#2a2a2a",
                                          highlightthickness=0, bd=0)
        self.progress_canvas.pack(fill="x")
        self.progress_canvas.bind("<Button-1>", self.seek)
        self.time_lbl = tk.Label(prog_frame, text="0:00 / 0:00",
                                  bg="#c0c0c0", fg="#7a2050",
                                  font=("MS Sans Serif", 8))
        self.time_lbl.pack(pady=(2, 0))
        controls = tk.Frame(self.content, bg="#c0c0c0")
        controls.pack(fill="x", padx=6, pady=6)
        tk.Button(controls, text="◀◀", width=4, font=("MS Sans Serif", 9),
                  command=self.prev_track).pack(side="left", padx=2)
        self.play_btn = tk.Button(controls, text="▶", width=4,
                                   font=("MS Sans Serif", 10, "bold"),
                                   fg="#7a2050", bg="#ffd6e8",
                                   activebackground="#ffb3d9",
                                   command=self.toggle_play)
        self.play_btn.pack(side="left", padx=2)
        tk.Button(controls, text="▶▶", width=4, font=("MS Sans Serif", 9),
                  command=self.next_track).pack(side="left", padx=2)
        tk.Button(controls, text="■", width=4, font=("MS Sans Serif", 9),
                  command=self.stop).pack(side="left", padx=2)
        vol_frame = tk.Frame(self.content, bg="#c0c0c0")
        vol_frame.pack(fill="x", padx=6, pady=2)
        tk.Label(vol_frame, text="Vol", bg="#c0c0c0", fg="#7a2050",
                 font=("MS Sans Serif", 8, "bold")).pack(side="left")
        self.volume = tk.Scale(vol_frame, from_=0, to=100, orient="horizontal",
                                showvalue=False, bg="#c0c0c0", bd=1,
                                highlightthickness=0, length=200,
                                troughcolor="#ffd6e8", activebackground="#ffb3d9",
                                command=self.set_volume)
        self.volume.set(70)
        self.volume.pack(side="left", fill="x", expand=True, padx=6)
        opts = tk.Frame(self.content, bg="#c0c0c0")
        opts.pack(fill="x", padx=6)
        self.shuffle_var = tk.BooleanVar(value=False)
        self.loop_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opts, text="Shuffle", variable=self.shuffle_var,
                       bg="#c0c0c0", fg="#7a2050", activebackground="#c0c0c0",
                       selectcolor="#ffd6e8",
                       font=("MS Sans Serif", 8)).pack(side="left")
        tk.Checkbutton(opts, text="Loop", variable=self.loop_var,
                       bg="#c0c0c0", fg="#7a2050", activebackground="#c0c0c0",
                       selectcolor="#ffd6e8",
                       font=("MS Sans Serif", 8)).pack(side="left", padx=10)
        tk.Button(opts, text="↻ Reload", font=("MS Sans Serif", 8),
                  command=self.reload).pack(side="right")
        bottom = tk.Frame(self.content, bg="#c0c0c0")
        bottom.pack(fill="both", expand=True, padx=6, pady=(8, 4))
        side = tk.Frame(bottom, bg="#c0c0c0", width=110)
        side.pack(side="left", fill="y", padx=(0, 4))
        side.pack_propagate(False)
        tk.Label(side, text="Folders", bg="#c0c0c0", fg="#7a2050",
                 anchor="w", font=("MS Sans Serif", 8, "bold")).pack(fill="x")
        side_inner = tk.Frame(side, bg="#808080", bd=2, relief="sunken")
        side_inner.pack(fill="both", expand=True)
        self.folder_list = tk.Listbox(side_inner, bg="white", fg="#7a2050",
                                       font=("MS Sans Serif", 8), activestyle="none",
                                       selectbackground="#ffb3d9",
                                       selectforeground="#7a2050",
                                       bd=0, highlightthickness=0)
        self.folder_list.pack(fill="both", expand=True)
        self.folder_list.bind("<<ListboxSelect>>", self.on_folder_select)
        pl_wrap = tk.Frame(bottom, bg="#c0c0c0")
        pl_wrap.pack(side="left", fill="both", expand=True)
        tk.Label(pl_wrap, text="Playlist", bg="#c0c0c0", fg="#7a2050",
                 anchor="w", font=("MS Sans Serif", 8, "bold")).pack(fill="x")
        pl_inner = tk.Frame(pl_wrap, bg="#808080", bd=2, relief="sunken")
        pl_inner.pack(fill="both", expand=True)
        self.playlist = tk.Listbox(pl_inner, bg="white", fg="#7a2050",
                                    font=("MS Sans Serif", 9), activestyle="none",
                                    bd=0, selectbackground="#ffb3d9",
                                    selectforeground="#7a2050",
                                    highlightthickness=0)
        self.playlist.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(pl_inner, command=self.playlist.yview)
        sb.pack(side="right", fill="y")
        self.playlist.config(yscrollcommand=sb.set)
        self.playlist.bind("<Double-Button-1>", self.play_selected)
        self.status_lbl = tk.Label(self.content, text="", bg="#c0c0c0",
                                     fg="#7a2050", font=("MS Sans Serif", 7), anchor="w")
        self.status_lbl.pack(fill="x", padx=6, pady=(0, 4))
        self.library = {"All": []}; self.folder_order = ["All"]
        self.current_folder = "All"; self.view_tracks = []
        self.current_index = -1; self.playing = False; self.paused = False
        self.elapsed = 0.0; self.duration = 0.0; self.last_tick = time.time()
        if not HAS_PYGAME:
            self.status_lbl.config(text="pygame not installed. Run: pip install pygame")
        self.scan_library(); self.refresh_folder_list(); self.select_folder("All")
        self.after(100, self.tick)

    def scan_library(self):
        self.library = {"All": []}
        if not os.path.isdir(MUSIC_DIR): return
        for root, dirs, files in os.walk(MUSIC_DIR):
            rel = os.path.relpath(root, MUSIC_DIR)
            top = None if rel == "." else rel.split(os.sep)[0]
            parts = [] if rel == "." else rel.split(os.sep)
            if any(p in self.EXCLUDED_FOLDERS for p in parts):
                dirs[:] = []; continue
            for name in sorted(files):
                if name.lower().endswith(self.AUDIO_EXTS):
                    full = os.path.join(root, name)
                    disp = name if rel == "." else rel.replace(os.sep, " / ") + " / " + name
                    self.library["All"].append((full, disp))
                    if top: self.library.setdefault(top, []).append((full, disp))
        self.folder_order = ["All"] + sorted(k for k in self.library if k != "All")

    def refresh_folder_list(self):
        self.folder_list.delete(0, tk.END)
        for name in self.folder_order:
            self.folder_list.insert(tk.END, f"{name} ({len(self.library.get(name, []))})")

    def select_folder(self, name):
        if name not in self.folder_order: name = "All"
        self.current_folder = name
        try:
            idx = self.folder_order.index(name)
            self.folder_list.selection_clear(0, tk.END)
            self.folder_list.selection_set(idx)
            self.folder_list.activate(idx)
        except Exception: pass
        self.view_tracks = list(self.library.get(name, []))
        self.refresh_playlist()

    def on_folder_select(self, event=None):
        sel = self.folder_list.curselection()
        if not sel: return
        name = self.folder_order[sel[0]]
        if name != self.current_folder: self.select_folder(name)

    def refresh_playlist(self):
        self.playlist.delete(0, tk.END)
        if not self.view_tracks:
            self.playlist.insert(tk.END, " (no tracks)")
            self.playlist.itemconfig(0, foreground="#888888")
            return
        for _, disp in self.view_tracks:
            self.playlist.insert(tk.END, "♪ " + disp)
        self.status_lbl.config(text=f"{self.current_folder}: {len(self.view_tracks)} track(s)")

    def reload(self):
        self.scan_library(); self.refresh_folder_list(); self.select_folder(self.current_folder)

    def play_index(self, idx):
        if not HAS_PYGAME or not self.view_tracks: return
        if idx < 0 or idx >= len(self.view_tracks): return
        self.stop_playback()
        path, disp = self.view_tracks[idx]
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.volume.get() / 100.0)
            pygame.mixer.music.play()
        except Exception as e:
            SOUNDS.error(); self.status_lbl.config(text=f"Error: {e}"); return
        self.current_index = idx; self.playing = True; self.paused = False
        self.elapsed = 0.0; self.last_tick = time.time()
        try:
            snd = pygame.mixer.Sound(path); self.duration = float(snd.get_length())
        except Exception: self.duration = 0.0
        self.now_playing.config(text="♪ " + disp)
        self.play_btn.config(text="❚❚")
        try:
            self.playlist.selection_clear(0, tk.END)
            self.playlist.selection_set(idx); self.playlist.see(idx)
        except Exception: pass

    def stop_playback(self):
        if HAS_PYGAME:
            try: pygame.mixer.music.stop()
            except Exception: pass
        self.playing = False; self.paused = False

    def stop(self):
        self.stop_playback(); self.elapsed = 0.0
        self.play_btn.config(text="▶"); self.update_progress()

    def toggle_play(self):
        if not self.view_tracks:
            self.reload()
            if not self.view_tracks: SOUNDS.error(); return
        if not self.playing:
            self.play_index(self.current_index if 0 <= self.current_index < len(self.view_tracks) else 0)
        elif self.paused:
            try:
                pygame.mixer.music.unpause(); self.paused = False
                self.last_tick = time.time(); self.play_btn.config(text="❚❚")
            except Exception: pass
        else:
            try:
                pygame.mixer.music.pause(); self.paused = True
                self.play_btn.config(text="▶")
            except Exception: pass

    def next_track(self):
        if not self.view_tracks: return
        idx = random.randrange(len(self.view_tracks)) if self.shuffle_var.get() else (self.current_index + 1) % len(self.view_tracks)
        self.play_index(idx)

    def prev_track(self):
        if not self.view_tracks: return
        idx = random.randrange(len(self.view_tracks)) if self.shuffle_var.get() else (self.current_index - 1) % len(self.view_tracks)
        self.play_index(idx)

    def play_selected(self, event=None):
        sel = self.playlist.curselection()
        if not sel: return
        self.play_index(sel[0])

    def set_volume(self, val):
        if HAS_PYGAME:
            try: pygame.mixer.music.set_volume(float(val) / 100.0)
            except Exception: pass

    def seek(self, event):
        if not self.playing or self.duration <= 0 or not HAS_PYGAME: return
        w = self.progress_canvas.winfo_width()
        if w <= 0: return
        pct = max(0.0, min(1.0, event.x / w))
        try:
            pygame.mixer.music.play(start=pct * self.duration)
            self.elapsed = pct * self.duration; self.last_tick = time.time()
            if self.paused: pygame.mixer.music.pause()
        except Exception: pass

    def update_progress(self):
        w = self.progress_canvas.winfo_width() or 400
        h = self.progress_canvas.winfo_height() or 14
        self.progress_canvas.delete("all")
        self.progress_canvas.create_rectangle(0, 0, w, h, fill="#2a2a2a", outline="")
        if self.duration > 0:
            pct = min(1.0, max(0.0, self.elapsed / self.duration))
            fill_w = int(w * pct)
            if fill_w > 0:
                self.progress_canvas.create_rectangle(0, 0, fill_w, h,
                                                       fill="#ff69b4", outline="")
            m1, s1 = divmod(int(self.elapsed), 60)
            m2, s2 = divmod(int(self.duration), 60)
            self.time_lbl.config(text=f"{m1}:{s1:02d} / {m2}:{s2:02d}")
        else:
            m1, s1 = divmod(int(self.elapsed), 60)
            self.time_lbl.config(text=f"{m1}:{s1:02d} / --:--")

    def tick(self):
        if not self.winfo_exists(): return
        try:
            now = time.time(); dt = now - self.last_tick; self.last_tick = now
            if self.playing and not self.paused:
                self.elapsed += dt
                if HAS_PYGAME:
                    try: busy = pygame.mixer.music.get_busy()
                    except Exception: busy = False
                    if not busy and self.elapsed > 0.5:
                        if self.loop_var.get(): self.play_index(self.current_index)
                        else: self.next_track()
            self.update_progress()
        except Exception as e: print("music tick error:", e)
        try: self.after(100, self.tick)
        except Exception: pass

    def _close(self):
        self.stop_playback(); super()._close()


# ============================================================
#  PAINT
# ============================================================
class PaintWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="untitled - Paint", width=640, height=480,
                         desktop=desktop)
        self.color = "#000000"; self.brush = 3; self.tool = "pencil"
        self.last = None; self.start_pos = None; self.preview_id = None
        toolbar = tk.Frame(self.content, bg="#c0c0c0"); toolbar.pack(fill="x")
        tools = [("✏", "pencil"), ("╱", "line"), ("▭", "rect"),
                 ("◯", "ellipse"), ("⌫", "eraser")]
        self.tool_btns = {}
        for icon, name in tools:
            b = tk.Button(toolbar, text=icon, width=2,
                          font=("MS Sans Serif", 10),
                          relief="sunken" if name == "pencil" else "raised",
                          command=lambda n=name: self.set_tool(n))
            b.pack(side="left", padx=1, pady=2); self.tool_btns[name] = b
        tk.Frame(toolbar, bg="#808080", width=2).pack(side="left", fill="y", padx=4, pady=2)
        for c in ["#000000", "#ffffff", "#ff0000", "#00ff00", "#0000ff",
                  "#ffff00", "#ff00ff", "#00ffff", "#ff8000", "#800080"]:
            tk.Button(toolbar, bg=c, width=2, height=1, bd=2, relief="raised",
                      command=lambda h=c: self.set_color(h)).pack(side="left", padx=1, pady=2)
        tk.Frame(toolbar, bg="#808080", width=2).pack(side="left", fill="y", padx=4, pady=2)
        self.brush_btns = {}
        for sz in (1, 3, 6, 12):
            b = tk.Button(toolbar, text=str(sz), width=2,
                          font=("MS Sans Serif", 7),
                          relief="sunken" if sz == 3 else "raised",
                          command=lambda s=sz: self.set_brush(s))
            b.pack(side="left", padx=1, pady=2); self.brush_btns[sz] = b
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
    def set_color(self, c): self.color = c
    def set_brush(self, s):
        self.brush = s
        for v, b in self.brush_btns.items():
            b.config(relief="sunken" if v == s else "raised")
    def clear(self): self.canvas.delete("all")
    def on_press(self, e):
        self.last = (e.x, e.y); self.start_pos = (e.x, e.y); self.preview_id = None
        if self.tool in ("pencil", "eraser"): self.draw_point(e.x, e.y)
    def draw_point(self, x, y):
        r = self.brush / 2
        fill = "white" if self.tool == "eraser" else self.color
        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=fill, outline=fill)
    def on_drag(self, e):
        if self.tool in ("pencil", "eraser"):
            x0, y0 = self.last
            fill = "white" if self.tool == "eraser" else self.color
            self.canvas.create_line(x0, y0, e.x, e.y, fill=fill,
                                    width=self.brush, capstyle="round", smooth=True)
            self.last = (e.x, e.y)
        else:
            if self.preview_id: self.canvas.delete(self.preview_id)
            sx, sy = self.start_pos
            if self.tool == "line":
                self.preview_id = self.canvas.create_line(sx, sy, e.x, e.y,
                                                          fill=self.color, width=self.brush)
            elif self.tool == "rect":
                self.preview_id = self.canvas.create_rectangle(sx, sy, e.x, e.y,
                                                                outline=self.color, width=self.brush)
            elif self.tool == "ellipse":
                self.preview_id = self.canvas.create_oval(sx, sy, e.x, e.y,
                                                          outline=self.color, width=self.brush)
    def on_release(self, e):
        self.preview_id = None; self.last = None


# ============================================================
#  COMMAND PROMPT
# ============================================================
class CommandPromptWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="Command Prompt", width=640, height=420,
                         desktop=desktop)
        self.desktop = desktop; self.fs = build_fs()
        self.cwd = ["C:"]; self.history = []; self.hist_idx = 0
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
        self.write("0W07 Command Prompt [Version 0.6]\n")
        self.write("(c) 2007 owlito. Type HELP for commands.\n\n")

    def prompt_str(self): return "\\".join(self.cwd) + ">"
    def write(self, s):
        self.out.config(state="normal"); self.out.insert("end", s)
        self.out.see("end"); self.out.config(state="disabled")
    def on_enter(self, event):
        cmd = self.entry.get(); self.entry.delete(0, "end")
        self.write(self.prompt_str() + cmd + "\n")
        if cmd.strip():
            self.history.append(cmd); self.hist_idx = len(self.history)
            self.run(cmd.strip())
        self.prompt_lbl.config(text=self.prompt_str())
        return "break"
    def hist_up(self, event):
        if not self.history: return "break"
        self.hist_idx = max(0, self.hist_idx - 1)
        self.entry.delete(0, "end"); self.entry.insert(0, self.history[self.hist_idx])
        return "break"
    def hist_down(self, event):
        if not self.history: return "break"
        self.hist_idx = min(len(self.history), self.hist_idx + 1)
        self.entry.delete(0, "end")
        if self.hist_idx < len(self.history): self.entry.insert(0, self.history[self.hist_idx])
        return "break"
    def resolve_node(self):
        node = self.fs
        for key in self.cwd: node = node[key]["children"]
        return node

    def run(self, cmd):
        parts = cmd.split()
        if not parts: return
        c = parts[0].lower(); args = parts[1:]
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
            if not args: self.write("\\".join(self.cwd) + "\n"); return
            target = args[0]
            if target == "..":
                if len(self.cwd) > 1: self.cwd.pop()
            elif target in (".", "\\"): pass
            else:
                node = self.resolve_node()
                match = next((k for k in node if k.lower() == target.lower()
                              and node[k]["type"] in ("drive", "folder")), None)
                if match: self.cwd.append(match)
                else: self.write("The system cannot find the path specified.\n")
        elif c == "cls":
            self.out.config(state="normal"); self.out.delete("1.0", "end")
            self.out.config(state="disabled")
        elif c == "echo": self.write(" ".join(args) + "\n")
        elif c == "ver":  self.write("0W07 [Version 0.6]\n")
        elif c == "date": self.write(time.strftime("%a %m/%d/%Y\n"))
        elif c == "time": self.write(time.strftime("%I:%M:%S %p\n"))
        elif c == "whoami": self.write(f"0w07\\{STATE.username}\n")
        elif c == "notepad": self.desktop.open_notepad()
        elif c in ("calc", "calculator"): self.desktop.open_calculator()
        elif c == "paint": self.desktop.open_paint()
        elif c in ("music", "player"): self.desktop.open_music_player()
        elif c in ("store", "shop"): self.desktop.open_store()
        elif c == "snake": self.desktop.open_snake()
        elif c == "pong": self.desktop.open_pong()
        elif c == "exit": self._close()
        else:
            self.write(f"'{parts[0]}' is not recognized.\n")


# ============================================================
#  NOTEPAD
# ============================================================
class NotepadWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="Untitled - Notepad", width=560, height=420,
                         desktop=desktop)
        self.desktop = desktop; self.filepath = None; self.dirty = False
        menu_bar = tk.Frame(self.content, bg="#c0c0c0"); menu_bar.pack(fill="x")
        def mb(label, builder):
            b = tk.Button(menu_bar, text=label, font=("MS Sans Serif", 8),
                          bg="#c0c0c0", relief="flat", padx=6,
                          command=lambda: builder(b))
            b.pack(side="left")
        mb("File", self.file_menu); mb("Edit", self.edit_menu)
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

    def on_typing(self, e): self.dirty = True; self.update_title()
    def update_title(self):
        name = os.path.basename(self.filepath) if self.filepath else "Untitled"
        self.set_title(f"{'*' if self.dirty else ''}{name} - Notepad")
    def update_status(self, e=None):
        try:
            line, col = self.text.index("insert").split(".")
            self.status.config(text=f"Ln {line}, Col {int(col)+1}")
        except Exception: pass
    def file_menu(self, anchor):
        m = self._popup(anchor)
        def add(label, cmd, sep=False):
            if sep: tk.Frame(m, height=1, bg="#808080").pack(fill="x", pady=2)
            tk.Button(m, text=label, anchor="w", bg="#c0c0c0", relief="flat",
                      font=("MS Sans Serif", 8), width=14,
                      command=lambda: (m.destroy(), cmd())).pack(fill="x", padx=2, pady=1)
        add("New", self.new_file); add("Open...", self.open_file)
        add("Save", self.save_file); add("Save As...", self.save_as)
        add("", None, sep=True); add("Exit", self._close)
    def edit_menu(self, anchor):
        m = self._popup(anchor)
        def add(label, cmd, sep=False):
            if sep: tk.Frame(m, height=1, bg="#808080").pack(fill="x", pady=2)
            tk.Button(m, text=label, anchor="w", bg="#c0c0c0", relief="flat",
                      font=("MS Sans Serif", 8), width=14,
                      command=lambda: (m.destroy(), cmd())).pack(fill="x", padx=2, pady=1)
        def ev(n):
            def go():
                try: self.text.event_generate(n)
                except Exception: pass
            return go
        add("Cut", ev("<<Cut>>")); add("Copy", ev("<<Copy>>")); add("Paste", ev("<<Paste>>"))
        add("", None, sep=True); add("Select All", lambda: self.text.tag_add("sel", "1.0", "end"))
    def _popup(self, anchor):
        m = tk.Toplevel(self); m.overrideredirect(True)
        m.geometry(f"+{anchor.winfo_rootx()}+{anchor.winfo_rooty()+anchor.winfo_height()}")
        m.configure(bg="#c0c0c0", relief="raised", bd=2)
        m.bind("<FocusOut>", lambda e: m.destroy())
        m.after(50, m.focus_force); return m
    def new_file(self):
        self.text.delete("1.0", "end"); self.filepath = None; self.dirty = False
        self.update_title()
    def open_file(self):
        p = filedialog.askopenfilename(filetypes=[("Text", "*.txt"),
                                                  ("Python", "*.py"), ("All", "*.*")])
        if not p: return
        try:
            with open(p, "r", encoding="utf-8") as f: content = f.read()
            self.text.delete("1.0", "end"); self.text.insert("1.0", content)
            self.filepath = p; self.dirty = False; self.update_title()
        except Exception as e:
            SOUNDS.error(); messagebox.showerror("Notepad", f"Could not open:\n{e}")
    def save_file(self):
        if not self.filepath: self.save_as(); return
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", "end-1c"))
            self.dirty = False; self.update_title()
        except Exception as e:
            SOUNDS.error(); messagebox.showerror("Notepad", f"Could not save:\n{e}")
    def save_as(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt",
                                          filetypes=[("Text", "*.txt"),
                                                     ("Python", "*.py"), ("All", "*.*")])
        if not p: return
        self.filepath = p; self.save_file()


# ============================================================
#  SNAKE
# ============================================================
class SnakeWindow(RetroWindow):
    CELL, COLS, ROWS = 18, 22, 20
    def __init__(self, master, desktop):
        w = self.CELL * self.COLS + 30; h = self.CELL * self.ROWS + 100
        super().__init__(master, title="Snake", width=w, height=h, desktop=desktop)
        top = tk.Frame(self.content, bg="#c0c0c0"); top.pack(fill="x", padx=6, pady=(6, 2))
        tk.Label(top, text="Score:", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(side="left")
        self.score_lbl = tk.Label(top, text="0", bg="#c0c0c0",
                                  font=("MS Sans Serif", 10, "bold"))
        self.score_lbl.pack(side="left", padx=4)
        tk.Button(top, text="New Game", font=("MS Sans Serif", 8),
                  command=self.reset).pack(side="right")
        self.canvas = tk.Canvas(self.content, width=self.CELL*self.COLS,
                                height=self.CELL*self.ROWS, bg="#1a0a1a",
                                highlightthickness=0, bd=0)
        self.canvas.pack(padx=6, pady=6)
        self._job = None; self.running = False
        self.bind("<Key>", self.on_key)
        self.bind("<Button-1>", lambda e: self.focus_force(), add="+")
        self.after(80, self.focus_force); self.reset()
    def reset(self):
        if self._job:
            try: self.after_cancel(self._job)
            except Exception: pass
            self._job = None
        mx, my = self.COLS // 2, self.ROWS // 2
        self.snake = [(mx, my), (mx-1, my), (mx-2, my)]
        self.direction = (1, 0); self.next_direction = (1, 0)
        self.food = self._spawn(); self.score = 0
        self.score_lbl.config(text="0"); self.game_over = False; self.running = True
        self.draw(); self._job = self.after(400, self.tick)
    def _spawn(self):
        occupied = set(self.snake)
        empty = [(x, y) for x in range(self.COLS) for y in range(self.ROWS)
                 if (x, y) not in occupied]
        return random.choice(empty) if empty else None
    def on_key(self, event):
        if self.game_over: return
        k = event.keysym.lower()
        m = {"up": (0,-1), "w": (0,-1), "down": (0,1), "s": (0,1),
             "left": (-1,0), "a": (-1,0), "right": (1,0), "d": (1,0)}
        if k in m:
            d = m[k]
            if (d[0]+self.direction[0], d[1]+self.direction[1]) == (0, 0): return
            self.next_direction = d
    def tick(self):
        if not self.running: return
        self.direction = self.next_direction
        hx, hy = self.snake[0]
        nx, ny = hx + self.direction[0], hy + self.direction[1]
        if nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS: return self.die()
        if (nx, ny) in self.snake[:-1]: return self.die()
        self.snake.insert(0, (nx, ny))
        if (nx, ny) == self.food:
            self.score += 10; self.score_lbl.config(text=str(self.score))
            self.food = self._spawn()
        else: self.snake.pop()
        self.draw()
        delay = max(60, 120 - self.score // 5)
        self._job = self.after(delay, self.tick)
    def draw(self):
        self.canvas.delete("all"); C = self.CELL
        for i, (x, y) in enumerate(self.snake):
            fill = "#ff9ec7" if i == 0 else f"#ff{max(0, 158-int(60*i/max(1,len(self.snake)))):02x}{max(0, 199-int(30*i/max(1,len(self.snake)))):02x}"
            self.canvas.create_rectangle(x*C+1, y*C+1, (x+1)*C-1, (y+1)*C-1,
                                          fill=fill, outline="#c85fa0")
        if self.food:
            fx, fy = self.food
            self.canvas.create_oval(fx*C+3, fy*C+3, (fx+1)*C-3, (fy+1)*C-3,
                                    fill="#ff69b4", outline="#ffb3d9", width=2)
        if self.game_over:
            self.canvas.create_rectangle(0, self.ROWS*C//2-30, self.COLS*C,
                                          self.ROWS*C//2+30, fill="#1a0a1a",
                                          outline="#ff69b4", width=2)
            self.canvas.create_text(self.COLS*C//2, self.ROWS*C//2,
                                    text=f"GAME OVER  —  Score {self.score}",
                                    fill="#ff69b4", font=("MS Sans Serif", 12, "bold"))
    def die(self):
        self.running = False; self.game_over = True; SOUNDS.error(); self.draw()
    def _close(self):
        self.running = False
        if self._job:
            try: self.after_cancel(self._job)
            except Exception: pass
            self._job = None
        super()._close()


# ============================================================
#  PONG
# ============================================================
class PongWindow(RetroWindow):
    W, H = 560, 380
    PW, PH, BALL, WIN_SCORE = 10, 60, 12, 7
    def __init__(self, master, desktop):
        super().__init__(master, title="Pong", width=self.W+20,
                         height=self.H+90, desktop=desktop)
        self._job = None; self.running = False
        self.player_score = 0; self.ai_score = 0; self.keys = set()
        top = tk.Frame(self.content, bg="#c0c0c0"); top.pack(fill="x", padx=6, pady=(4, 0))
        self.score_lbl = tk.Label(top, text="0   :   0", bg="#c0c0c0",
                                   font=("MS Sans Serif", 14, "bold"))
        self.score_lbl.pack(side="left")
        tk.Label(top, text="W/S or arrows · First to 7 wins", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(side="right")
        self.canvas = tk.Canvas(self.content, width=self.W, height=self.H,
                                bg="#1a0a1a", highlightthickness=0)
        self.canvas.pack(padx=6, pady=6)
        self.bind("<Key>", self.on_key)
        self.bind("<KeyRelease>", self.on_key_release)
        self.bind("<Button-1>", lambda e: self.focus_force(), add="+")
        self.after(80, self.focus_force); self.new_round(first=True)
    def new_round(self, first=False):
        if not first and self._job:
            try: self.after_cancel(self._job)
            except Exception: pass
            self._job = None
        self.py = self.H/2; self.ay = self.H/2
        self.bx = self.W/2; self.by = self.H/2
        dx = random.choice([-1, 1]); dy = random.choice([-1, 1]) * random.uniform(0.4, 0.9)
        self.bdx = dx * 5; self.bdy = dy * 5
        self.running = True; self.draw(); self._job = self.after(30, self.tick)
    def on_key(self, event):
        k = event.keysym.lower()
        if k in ("up", "w", "down", "s"): self.keys.add(k); return "break"
    def on_key_release(self, event): self.keys.discard(event.keysym.lower())
    def tick(self):
        if not self.running: return
        if "up" in self.keys or "w" in self.keys: self.py = max(self.PH/2, self.py - 8)
        if "down" in self.keys or "s" in self.keys: self.py = min(self.H - self.PH/2, self.py + 8)
        diff = self.by - self.ay
        self.ay += max(-5, min(5, diff * 0.12))
        self.ay = max(self.PH/2, min(self.H - self.PH/2, self.ay))
        self.bx += self.bdx; self.by += self.bdy
        if self.by - self.BALL/2 <= 0 or self.by + self.BALL/2 >= self.H: self.bdy = -self.bdy
        if self.bx - self.BALL/2 <= 20 + self.PW/2 and abs(self.by - self.py) < self.PH/2:
            self.bdx = abs(self.bdx) * 1.05
            self.bdy += (self.by - self.py) * 0.1
            self.bx = 20 + self.PW/2 + self.BALL/2
        if self.bx + self.BALL/2 >= self.W - 20 - self.PW/2 and abs(self.by - self.ay) < self.PH/2:
            self.bdx = -abs(self.bdx) * 1.05
            self.bdy += (self.by - self.ay) * 0.1
            self.bx = self.W - 20 - self.PW/2 - self.BALL/2
        if self.bx < 0: self.ai_score += 1; return self.end_round()
        if self.bx > self.W: self.player_score += 1; return self.end_round()
        self.draw(); self._job = self.after(16, self.tick)
    def draw(self):
        c = self.canvas; c.delete("all")
        for y in range(0, self.H, 20):
            c.create_line(self.W/2, y, self.W/2, y+10, fill="#4a2a4a", width=2)
        c.create_rectangle(20-self.PW/2, self.py-self.PH/2, 20+self.PW/2, self.py+self.PH/2,
                           fill="#ff9ec7", outline="")
        c.create_rectangle(self.W-20-self.PW/2, self.ay-self.PH/2, self.W-20+self.PW/2, self.ay+self.PH/2,
                           fill="#c85fa0", outline="")
        c.create_oval(self.bx-self.BALL/2, self.by-self.BALL/2, self.bx+self.BALL/2, self.by+self.BALL/2,
                      fill="#ffd6e8", outline="#ff69b4", width=2)
        self.score_lbl.config(text=f"{self.player_score}   :   {self.ai_score}")
    def end_round(self):
        self.running = False; self.draw()
        winner = None
        if self.player_score >= self.WIN_SCORE: winner = "You win!"
        elif self.ai_score >= self.WIN_SCORE: winner = "CPU wins!"
        if winner:
            self.canvas.create_rectangle(self.W/2-110, self.H/2-30, self.W/2+110, self.H/2+30,
                                          fill="#1a0a1a", outline="#ff69b4", width=2)
            self.canvas.create_text(self.W/2, self.H/2, text=winner, fill="#ff69b4",
                                     font=("MS Sans Serif", 18, "bold"))
            self.after(2500, self._reset)
        else: self.after(800, self.new_round)
    def _reset(self):
        self.player_score = 0; self.ai_score = 0; self.new_round(first=True)
    def _close(self):
        self.running = False
        if self._job:
            try: self.after_cancel(self._job)
            except Exception: pass
            self._job = None
        super()._close()


# ============================================================
#  FILE EXPLORER
# ============================================================
class FileExplorerWindow(RetroWindow):
    def __init__(self, master, desktop):
        super().__init__(master, title="My Computer", width=520, height=380,
                         desktop=desktop)
        self.fs = build_fs(); self.path = []
        bar = tk.Frame(self.content, bg="#c0c0c0"); bar.pack(fill="x", padx=4, pady=(4, 2))
        tk.Button(bar, text="Up", font=("MS Sans Serif", 8),
                  command=self.go_up).pack(side="left")
        tk.Button(bar, text="Refresh", font=("MS Sans Serif", 8),
                  command=self.refresh).pack(side="left", padx=4)
        self.addr = tk.Label(bar, text="My Computer", bg="white", anchor="w",
                             relief="sunken", bd=1, font=("MS Sans Serif", 8))
        self.addr.pack(side="left", fill="x", expand=True, padx=6)
        body = tk.Frame(self.content, bg="#c0c0c0"); body.pack(fill="both", expand=True, padx=4, pady=4)
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
        self.status.pack(fill="x", padx=6); self.refresh()
    def current_node(self):
        node = self.fs
        for k in self.path: node = node[k]["children"]
        return node
    def full_path_str(self):
        return "My Computer" + ("" if not self.path else "\\" + "\\".join(self.path))
    def refresh(self):
        self.listbox.delete(0, tk.END); node = self.current_node()
        self.addr.config(text=self.full_path_str())
        self.items = sorted(node.keys())
        for name in self.items:
            meta = node[name]
            prefix = self.icon_for(meta["type"], name)
            self.listbox.insert(tk.END, f"{prefix}  {name}")
        self.status.config(text=f"{len(self.items)} item(s)")
    @staticmethod
    def icon_for(kind, name):
        if kind == "drive": return "[D]"
        if kind == "folder": return "[+]"
        if name.endswith((".png", ".gif", ".jpg", ".jpeg")): return "[I]"
        if name.endswith((".mp3", ".ogg", ".wav", ".flac")): return "[♪]"
        if name.endswith(".py"): return "[P]"
        if name.endswith(".txt"): return "[T]"
        return "[F]"
    def on_double(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        name = self.items[sel[0]]
        meta = self.current_node()[name]
        if meta["type"] in ("folder", "drive"):
            self.path.append(name); self.refresh()
        else:
            SOUNDS.error(); self.status.config(text=f"Cannot open {name}")
    def go_up(self):
        if self.path: self.path.pop(); self.refresh()


# ============================================================
#  DESKTOP
# ============================================================
class OW07Desktop:
    def __init__(self):
        self.root = tk.Tk()
        self.root.report_callback_exception = _tk_exception_handler
        self.root.withdraw()
        self.root.title("0W07")
        self.root.configure(bg=STATE.desktop_color)

        self.fullscreen = True
        try: self.root.attributes("-fullscreen", True)
        except Exception: self.root.geometry("1024x720")

        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.windows = []
        self.start_menu = None
        self.programs_submenu = None
        self.settings_win = None
        self.desktop_menu = None
        self.wallpaper_label = None
        self.icon_canvases = []
        self.selected_icon = None
        self.login_screen = None
        self.boot_screen = None

        self.root.bind("<Button-3>", self.show_desktop_menu)
        self.root.bind("<Button-1>", self.deselect_icons, add="+")

        self.apply_wallpaper()
        self.mascots = MascotManager(self.root)

        # Taskbar
        self.taskbar = tk.Frame(self.root, bg="#ffd6e8", height=TASKBAR_H,
                                relief="raised", bd=2)
        self.taskbar.pack(side="bottom", fill="x")
        self.taskbar.pack_propagate(False)
        self.start_btn = tk.Button(self.taskbar, text="♥ Start", bg="#ffb3d9",
                                   fg="#7a2050", relief="raised", bd=2,
                                   activebackground="#ff69b4",
                                   font=("MS Sans Serif", 8, "bold"),
                                   command=self.toggle_start_menu)
        self.start_btn.pack(side="left", padx=2, pady=2)
        tk.Frame(self.taskbar, bg="#c85fa0", width=2).pack(side="left", fill="y", padx=2, pady=2)
        self.taskbar_windows = tk.Frame(self.taskbar, bg="#ffd6e8")
        self.taskbar_windows.pack(side="left", fill="both", expand=True)
        self.clock = tk.Label(self.taskbar, bg="#ffd6e8", fg="#7a2050",
                              font=("MS Sans Serif", 8, "bold"))
        self.clock.pack(side="right", padx=5)
        self.update_clock()

        self.build_desktop_icons()
        self.start_flow()

    def start_flow(self):
        # 1. Boot (unless skipped) → 2. Login → 3. Desktop
        if STATE.skip_boot:
            self.show_login()
        else:
            self.boot_screen = BootScreen(self.root, on_done=self.show_login)

    def show_login(self):
        self.login_screen = LoginScreen(self.root,
                                         on_login=self.finish_login,
                                         on_shutdown=self.root.destroy)

    def finish_login(self):
        self.root.deiconify()
        self.open_notepad()

    # ---------- Fullscreen ----------
    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        try: self.root.attributes("-fullscreen", self.fullscreen)
        except Exception: pass
    def exit_fullscreen(self, event=None):
        if self.fullscreen:
            self.fullscreen = False
            try: self.root.attributes("-fullscreen", False)
            except Exception: pass

    # ---------- Wallpaper ----------
    def apply_wallpaper(self):
        if self.wallpaper_label:
            try: self.wallpaper_label.destroy()
            except Exception: pass
            self.wallpaper_label = None
        if not STATE.wallpaper_path or not os.path.isfile(STATE.wallpaper_path): return
        sw = self.root.winfo_screenwidth(); sh = self.root.winfo_screenheight()
        try:
            if HAS_PIL:
                img = Image.open(STATE.wallpaper_path)
                img = img.resize((sw, sh), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
            else:
                photo = tk.PhotoImage(file=STATE.wallpaper_path)
        except Exception as e:
            print("wallpaper failed:", e); return
        lbl = tk.Label(self.root, image=photo, bd=0, bg=STATE.desktop_color)
        lbl.image = photo
        lbl.place(x=0, y=0, width=sw, height=sh); lbl.lower()
        self.wallpaper_label = lbl

    # ---------- Desktop icons ----------
    def build_desktop_icons(self):
        for cv in self.icon_canvases:
            try: cv.destroy()
            except Exception: pass
        self.icon_canvases = []
        self.selected_icon = None

        icons = [
            ("My Computer", "🖥",  "#ffd6e8", "✨", self.open_file_explorer),
            ("Store",       "🛍",  "#ffd4e8", "♥",  self.open_store),
            ("Music",       "🎧", "#ffd4e8", "♪",  self.open_music_player),
            ("Notepad",     "📝", "#ffe4b5", "💕", self.open_notepad),
            ("Paint",       "🎨", "#e0d4ff", "🌸", self.open_paint),
            ("Command",     "💻", "#d4f0ff", "⭐", self.open_cmd),
            ("Calculator",  "🧮", "#fff5b8", "✨", self.open_calculator),
            ("Snake",       "🐍", "#c8f5c8", "💚", self.open_snake),
            ("Pong",        "🏓", "#ffd4d4", "💗", self.open_pong),
            ("Settings",    "⚙",  "#e8e8ff", "🌸", self.open_settings),
            ("Recycle Bin", "🗑",  "#ffd6e8", "💫", self.open_recycle),
        ]

        # Append installed store apps
        for app_id in sorted(STATE.installed_apps):
            app = get_store_app(app_id)
            if not app: continue
            launcher = getattr(self, f"open_{app_id}", None)
            if launcher:
                icons.append((app["name"], app["icon"], app["pastel"],
                              app["accent"], launcher))

        margin_x, margin_y = 20, 20
        dx, dy = 100, 90
        per_row = max(1, (self.root.winfo_screenwidth() - margin_x * 2) // dx)

        for i, (label, emoji, pastel, accent, cmd) in enumerate(icons):
            x = margin_x + (i % per_row) * dx
            y = margin_y + (i // per_row) * dy
            cv = tk.Canvas(self.root, width=90, height=80,
                           bg=STATE.desktop_color, highlightthickness=0, bd=0)
            cv.place(x=x, y=y)
            cv._bg_rect = cv.create_rectangle(0, 0, 90, 80, fill="", outline="")
            cv.create_oval(20, 4, 70, 54, fill=pastel, outline="#ffffff", width=2)
            cv.create_text(45, 30, text=emoji, font=("Segoe UI Emoji", 22))
            cv.create_text(72, 10, text=accent, font=("Segoe UI Emoji", 9))
            cv.create_text(46, 67, text=label, fill="#003333",
                           font=("MS Sans Serif", 8, "bold"),
                           width=88, justify="center")
            cv.create_text(45, 66, text=label, fill="white",
                           font=("MS Sans Serif", 8), width=88, justify="center")

            def on_click(e, c=cv): self.select_icon(c)
            def on_double(e, c=cmd):
                SOUNDS.click(); c()
            cv.bind("<Button-1>", on_click)
            cv.bind("<Double-Button-1>", on_double)
            self.icon_canvases.append(cv)

    def select_icon(self, canvas):
        if self.selected_icon and self.selected_icon is not canvas:
            try: self.selected_icon.itemconfig(self.selected_icon._bg_rect, fill="")
            except Exception: pass
        self.selected_icon = canvas
        try: canvas.itemconfig(canvas._bg_rect, fill="#c85fa0", outline="#ffffff")
        except Exception: pass

    def deselect_icons(self, event=None):
        if self.selected_icon is None: return
        w = event.widget if event else None
        if w in self.icon_canvases: return
        try: self.selected_icon.itemconfig(self.selected_icon._bg_rect, fill="", outline="")
        except Exception: pass
        self.selected_icon = None

    def recolor_icons(self, color):
        for cv in self.icon_canvases:
            try: cv.configure(bg=color)
            except Exception: pass

    # ---------- Desktop menu ----------
    def show_desktop_menu(self, event):
        self.close_desktop_menu()
        m = tk.Toplevel(self.root); m.overrideredirect(True)
        m.geometry(f"+{event.x_root}+{event.y_root}")
        m.configure(bg="#ffd6e8", relief="raised", bd=2)
        self.desktop_menu = m
        def add(label, cmd):
            tk.Button(m, text=label, anchor="w", bg="#ffd6e8", fg="#7a2050",
                      relief="flat", activebackground="#ffb3d9",
                      font=("MS Sans Serif", 8),
                      command=lambda: (self.close_desktop_menu(), cmd())
                      ).pack(fill="x", padx=2, pady=1)
        add("♥ Refresh", self.refresh_desktop)
        add("🌸 Change background", self.pick_wallpaper)
        add("✨ Desktop colour...", lambda: self.open_settings_tab("Appearance"))
        add("🛍 Open Store", self.open_store)
    def close_desktop_menu(self):
        if self.desktop_menu:
            try: self.desktop_menu.destroy()
            except Exception: pass
            self.desktop_menu = None
    def refresh_desktop(self):
        self.close_desktop_menu(); self.build_desktop_icons()
        if STATE.mascots_enabled: self.mascots.spawn(STATE.mascot_count)
    def pick_wallpaper(self):
        p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.gif *.jpg *.jpeg"), ("All", "*.*")])
        if p:
            STATE.wallpaper_path = p; self.apply_wallpaper(); persist_state()

    # ---------- Window registry ----------
    def register_window(self, win, title):
        self.windows.append(win)
        btn = tk.Button(self.taskbar_windows, text=self._short(title),
                        bg="#ffd6e8", fg="#7a2050", relief="raised", bd=2,
                        anchor="w", activebackground="#ffb3d9",
                        font=("MS Sans Serif", 8), width=16,
                        command=lambda w=win: self.taskbar_click(w))
        btn.pack(side="left", padx=1, pady=2)
        win.taskbar_btn = btn
    def unregister_window(self, win):
        if win in self.windows: self.windows.remove(win)
        if win.taskbar_btn:
            try: win.taskbar_btn.destroy()
            except Exception: pass
            win.taskbar_btn = None
    def set_taskbar_state(self, win, minimized=False):
        if not win.taskbar_btn: return
        try: win.taskbar_btn.config(relief="sunken" if minimized else "raised")
        except Exception: pass
    def highlight_taskbar(self, win):
        for w in self.windows:
            if w.taskbar_btn:
                try:
                    if w is win and not w.minimized: w.taskbar_btn.config(relief="sunken")
                    elif w is not win: w.taskbar_btn.config(relief="raised")
                except Exception: pass
    def taskbar_click(self, win):
        SOUNDS.click()
        if win.minimized: win.restore()
        else: win.lift(); win._focus()
    @staticmethod
    def _short(text, n=16):
        return text if len(text) <= n else text[:n-1] + "..."

    def update_clock(self):
        if STATE.show_clock:
            self.clock.config(text=time.strftime("%I:%M %p"))
        else: self.clock.config(text="")
        self.root.after(1000, self.update_clock)

    # ---------- Start menu ----------
    def toggle_start_menu(self):
        SOUNDS.click()
        if self.start_menu: self.close_start_menu()
        else: self.open_start_menu()
    def open_start_menu(self):
        m = tk.Toplevel(self.root); m.overrideredirect(True)
        sh = self.root.winfo_screenheight(); menu_h = 320
        y = max(0, sh - TASKBAR_H - menu_h)
        m.geometry(f"200x{menu_h}+0+{y}")
        m.configure(bg="#ffd6e8", relief="raised", bd=2)
        self.start_menu = m
        header = tk.Frame(m, bg="#c85fa0", height=30)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text=f"♥ 0W07 ♥", bg="#c85fa0", fg="white",
                 font=("MS Sans Serif", 10, "bold")).pack(side="left", padx=5)
        tk.Label(header, text=STATE.username, bg="#c85fa0", fg="#ffd6e8",
                 font=("MS Sans Serif", 8)).pack(side="right", padx=5)
        for name in ["Programs", "Store", "Documents", "Settings", "Find",
                     "Help", "Run...", "Shut Down..."]:
            tk.Button(m, text=name, anchor="w", bg="#ffd6e8", fg="#7a2050",
                      relief="flat", activebackground="#ffb3d9",
                      font=("MS Sans Serif", 8),
                      command=lambda n=name: self.start_item(n)
                      ).pack(fill="x", padx=2, pady=1)
    def close_start_menu(self):
        self.close_programs_submenu()
        if self.start_menu:
            try: self.start_menu.destroy()
            except Exception: pass
            self.start_menu = None
    def close_programs_submenu(self):
        if self.programs_submenu:
            try: self.programs_submenu.destroy()
            except Exception: pass
            self.programs_submenu = None
    def start_item(self, name):
        SOUNDS.click()
        sx = self.start_menu.winfo_x(); sy = self.start_menu.winfo_y()
        sw = self.start_menu.winfo_width(); self.close_start_menu()
        if name == "Programs": self.show_programs_submenu(sx + sw, sy + 40)
        elif name == "Store": self.open_store()
        elif name == "Documents": self.open_documents()
        elif name == "Settings": self.open_settings()
        elif name == "Find": self.open_find()
        elif name == "Help": self.open_help()
        elif name == "Run...": self.open_run()
        elif name == "Shut Down...": self.open_shutdown()
    def show_programs_submenu(self, x, y):
        sm = tk.Toplevel(self.root); sm.overrideredirect(True)
        sm.geometry(f"180x220+{x}+{y}")
        sm.configure(bg="#ffd6e8", relief="raised", bd=2)
        self.programs_submenu = sm
        apps = [("Music Player", self.open_music_player),
                ("Notepad", self.open_notepad),
                ("Paint", self.open_paint),
                ("Command Prompt", self.open_cmd),
                ("Calculator", self.open_calculator),
                ("File Explorer", self.open_file_explorer),
                ("Snake", self.open_snake),
                ("Pong", self.open_pong)]
        for label, cmd in apps:
            tk.Button(sm, text=label, anchor="w", bg="#ffd6e8", fg="#7a2050",
                      relief="flat", activebackground="#ffb3d9",
                      font=("MS Sans Serif", 8),
                      command=lambda c=cmd: (SOUNDS.click(),
                                             self.close_programs_submenu(), c())
                      ).pack(fill="x", padx=2, pady=1)

    # ---------- Apps ----------
    def open_store(self): self.open_music_player.__self__  # placeholder
    def open_music_player(self): MusicPlayerWindow(self.root, desktop=self)
    def open_notepad(self): NotepadWindow(self.root, desktop=self)
    def open_paint(self): PaintWindow(self.root, desktop=self)
    def open_cmd(self): CommandPromptWindow(self.root, desktop=self)
    def open_snake(self): SnakeWindow(self.root, desktop=self)
    def open_pong(self): PongWindow(self.root, desktop=self)
    def open_file_explorer(self): FileExplorerWindow(self.root, desktop=self)
    def open_tetris(self): TetrisWindow(self.root, desktop=self)
    def open_clock(self): ClockWindow(self.root, desktop=self)
    def open_dice(self): DiceWindow(self.root, desktop=self)

    def open_store(self):
        StoreWindow(self.root, desktop=self)

    def open_calculator(self):
        win = RetroWindow(self.root, title="Calculator", width=220, height=280,
                          desktop=self)
        display = tk.Entry(win.content, font=("MS Sans Serif", 12),
                           justify="right", relief="sunken", bd=2,
                           bg="#fff8fc", fg="#7a2050", insertbackground="#c85fa0")
        display.pack(fill="x", padx=4, pady=4)
        def press(char):
            if char == "=":
                try:
                    r = str(eval(display.get()))
                    display.delete(0, tk.END); display.insert(0, r)
                except Exception:
                    SOUNDS.error(); display.delete(0, tk.END); display.insert(0, "error")
            elif char == "C": display.delete(0, tk.END)
            else: display.insert(tk.END, char)
        grid = tk.Frame(win.content, bg="#c0c0c0")
        grid.pack(expand=True, fill="both", padx=4, pady=4)
        keys = [["7","8","9","/"],["4","5","6","*"],
                ["1","2","3","-"],["0",".","=","+"]]
        for r, row in enumerate(keys):
            for c, k in enumerate(row):
                tk.Button(grid, text=k, width=4, height=2,
                          font=("MS Sans Serif", 9),
                          command=lambda ch=k: press(ch)).grid(row=r, column=c, padx=1, pady=1)
        tk.Button(win.content, text="C", font=("MS Sans Serif", 9),
                  command=lambda: press("C")).pack(fill="x", padx=4, pady=(0, 4))

    def open_recycle(self):
        win = RetroWindow(self.root, title="Recycle Bin", width=380, height=260,
                          desktop=self)
        tk.Label(win.content, text="🗑  Recycle Bin is empty.",
                 bg="#c0c0c0", font=("MS Sans Serif", 10)).pack(pady=40)

    # ============================================================
    #  SETTINGS
    # ============================================================
    def open_settings(self): self.open_settings_tab("Appearance")
    def open_settings_tab(self, tab_name):
        if self.settings_win and self.settings_win.winfo_exists():
            self.settings_win.lift(); self._show_tab(tab_name); return
        self.settings_win = RetroWindow(
            self.root, title="Settings - 0W07", width=520, height=460,
            x=200, y=80, desktop=self,
            on_close=lambda: setattr(self, "settings_win", None))
        win = self.settings_win
        tab_bar = tk.Frame(win.content, bg="#c0c0c0"); tab_bar.pack(fill="x")
        body = tk.Frame(win.content, bg="#c0c0c0"); body.pack(fill="both", expand=True)
        tabs = {}
        def show(name):
            for f in tabs.values(): f.pack_forget()
            tabs[name].pack(fill="both", expand=True)
        self._show_tab = show
        for name in ["Appearance", "Desktop", "Mascots", "Sounds", "Account", "About"]:
            f = tk.Frame(body, bg="#c0c0c0"); tabs[name] = f
            tk.Button(tab_bar, text=name, font=("MS Sans Serif", 8),
                      relief="raised", bg="#ffd6e8", fg="#7a2050", bd=2,
                      activebackground="#ffb3d9",
                      command=lambda n=name: show(n)).pack(side="left", padx=1, pady=2)

        # APPEARANCE
        ap = tabs["Appearance"]
        tk.Label(ap, text="Text size", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        size_row = tk.Frame(ap, bg="#c0c0c0"); size_row.pack(anchor="w", padx=10)
        scale_btns = {}
        def set_scale(new):
            old = STATE.text_scale
            if old == new: return
            rescale_fonts(self.root, new/old); STATE.text_scale = new
            for v, b in scale_btns.items():
                b.config(relief="sunken" if v == new else "raised")
            persist_state()
        for label, value in [("Small", 0.8), ("Normal", 1.0), ("Large", 1.25), ("Huge", 1.5)]:
            b = tk.Button(size_row, text=label, font=("MS Sans Serif", 8),
                          width=8, bd=2, command=lambda v=value: set_scale(v))
            b.pack(side="left", padx=2)
            b.config(relief="sunken" if value == STATE.text_scale else "raised")
            scale_btns[value] = b
        tk.Label(ap, text="Desktop colour", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")).pack(anchor="w", padx=10, pady=(16, 2))
        color_row = tk.Frame(ap, bg="#c0c0c0"); color_row.pack(anchor="w", padx=10)
        def set_color(hexval):
            STATE.desktop_color = hexval; STATE.wallpaper_path = None
            self.apply_wallpaper(); self.root.configure(bg=hexval)
            self.mascots.recolor(hexval); self.recolor_icons(hexval)
            persist_state()
        for hexval in ["#008080", "#ffb3d9", "#c85fa0", "#3a1a4d", "#1a1a2e", "#000000"]:
            tk.Button(color_row, bg=hexval, width=3, height=1, bd=2,
                      relief="raised", command=lambda h=hexval: set_color(h)
                      ).pack(side="left", padx=2)
        def pick_custom():
            chosen = colorchooser.askcolor(color=STATE.desktop_color, title="Pick desktop colour")
            if chosen and chosen[1]: set_color(chosen[1])
        tk.Button(ap, text="Custom...", font=("MS Sans Serif", 8),
                  command=pick_custom).pack(anchor="w", padx=10, pady=(6, 0))
        def reset_all():
            old = STATE.text_scale
            if old != 1.0:
                rescale_fonts(self.root, 1.0/old); STATE.text_scale = 1.0
            for v, b in scale_btns.items():
                b.config(relief="sunken" if v == 1.0 else "raised")
            set_color("#008080"); STATE.show_clock = True
            STATE.mascots_enabled = False; self.mascots.clear()
            STATE.skip_boot = False; STATE.wallpaper_path = None
            self.apply_wallpaper(); persist_state()
        tk.Button(ap, text="Reset to defaults", font=("MS Sans Serif", 8),
                  command=reset_all).pack(anchor="w", padx=10, pady=(24, 0))

        # DESKTOP
        dt = tabs["Desktop"]
        tk.Label(dt, text="Taskbar", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        def toggle_clock():
            STATE.show_clock = not STATE.show_clock
            clock_btn.config(text=f"Clock: {'ON' if STATE.show_clock else 'OFF'}")
            persist_state()
        clock_btn = tk.Button(dt, font=("MS Sans Serif", 8),
                              text=f"Clock: {'ON' if STATE.show_clock else 'OFF'}",
                              command=toggle_clock)
        clock_btn.pack(anchor="w", padx=10)
        tk.Label(dt, text="Boot", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")).pack(anchor="w", padx=10, pady=(16, 2))
        def toggle_skip_boot():
            STATE.skip_boot = not STATE.skip_boot
            skip_btn.config(text=f"Skip boot screen: {'ON' if STATE.skip_boot else 'OFF'}")
        skip_btn = tk.Button(dt, font=("MS Sans Serif", 8),
                             text=f"Skip boot screen: {'ON' if STATE.skip_boot else 'OFF'}",
                             command=toggle_skip_boot)
        skip_btn.pack(anchor="w", padx=10)
        tk.Label(dt, text="Wallpaper", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")).pack(anchor="w", padx=10, pady=(16, 2))
        wall_row = tk.Frame(dt, bg="#c0c0c0"); wall_row.pack(anchor="w", padx=10)
        def choose_wall():
            p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.gif *.jpg *.jpeg"), ("All", "*.*")])
            if p:
                STATE.wallpaper_path = p; self.apply_wallpaper(); persist_state()
        def clear_wall():
            STATE.wallpaper_path = None; self.apply_wallpaper()
            self.root.configure(bg=STATE.desktop_color)
            self.mascots.recolor(STATE.desktop_color); self.recolor_icons(STATE.desktop_color)
            persist_state()
        tk.Button(wall_row, text="Choose image...", font=("MS Sans Serif", 8),
                  command=choose_wall).pack(side="left", padx=(0, 4))
        tk.Button(wall_row, text="Clear", font=("MS Sans Serif", 8),
                  command=clear_wall).pack(side="left")

        # MASCOTS
        mc = tabs["Mascots"]
        tk.Label(mc, text="Desktop mascots", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        tk.Label(mc, text="Click a mascot to hear a random anime fact.",
                 bg="#c0c0c0", font=("MS Sans Serif", 8),
                 wraplength=460, justify="left").pack(anchor="w", padx=10)
        def refresh_mascot_btn():
            mascot_btn.config(text=f"Mascots: {'ON' if STATE.mascots_enabled else 'OFF'}")
        def toggle_mascots():
            STATE.mascots_enabled = not STATE.mascots_enabled
            if STATE.mascots_enabled: self.mascots.spawn(STATE.mascot_count)
            else: self.mascots.clear()
            refresh_mascot_btn(); persist_state()
        mascot_btn = tk.Button(mc, font=("MS Sans Serif", 8),
                               text=f"Mascots: {'ON' if STATE.mascots_enabled else 'OFF'}",
                               command=toggle_mascots)
        mascot_btn.pack(anchor="w", padx=10, pady=(6, 0))
        tk.Label(mc, text="How many?", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(anchor="w", padx=10, pady=(10, 0))
        count_row = tk.Frame(mc, bg="#c0c0c0"); count_row.pack(anchor="w", padx=10)
        count_btns = {}
        def set_count(n):
            STATE.mascot_count = n
            for v, b in count_btns.items():
                b.config(relief="sunken" if v == n else "raised")
            if STATE.mascots_enabled: self.mascots.spawn(n)
            persist_state()
        for n in [1, 2, 3, 5]:
            b = tk.Button(count_row, text=str(n), width=3,
                          font=("MS Sans Serif", 8),
                          relief="sunken" if n == STATE.mascot_count else "raised",
                          command=lambda v=n: set_count(v))
            b.pack(side="left", padx=2); count_btns[n] = b

        # SOUNDS
        sn = tabs["Sounds"]
        tk.Label(sn, text="Sound", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        tk.Label(sn, text="Drop sound files into assets/music/sfx/\nnamed: startup, click, mascot, error, shutdown.",
                 bg="#c0c0c0", font=("MS Sans Serif", 7), justify="left"
                 ).pack(anchor="w", padx=10)
        tk.Label(sn, text=f"Folder: {SFX_DIR}", bg="#c0c0c0",
                 font=("MS Sans Serif", 7), justify="left").pack(anchor="w", padx=10, pady=(0, 8))
        def make_toggle(parent, label, attr, test_fn=None):
            row = tk.Frame(parent, bg="#c0c0c0")
            row.pack(anchor="w", padx=10, pady=2, fill="x")
            def flip():
                setattr(STATE, attr, not getattr(STATE, attr))
                btn.config(text=f"{label}: {'ON' if getattr(STATE, attr) else 'OFF'}")
            btn = tk.Button(row, font=("MS Sans Serif", 8), width=18,
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

        # ACCOUNT
        ac = tabs["Account"]
        tk.Label(ac, text="Account", bg="#c0c0c0",
                 font=("MS Sans Serif", 8, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        tk.Label(ac, text="Username", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(anchor="w", padx=10)
        name_var = tk.StringVar(value=STATE.username)
        name_entry = tk.Entry(ac, textvariable=name_var, font=("MS Sans Serif", 10),
                              bg="#fff8fc", fg="#7a2050", relief="sunken", bd=2, width=24)
        name_entry.pack(anchor="w", padx=10, pady=(2, 6))
        def save_name():
            STATE.username = name_var.get().strip() or "owlito"
            persist_state(); SOUNDS.click()
        tk.Button(ac, text="Save", font=("MS Sans Serif", 8),
                  command=save_name).pack(anchor="w", padx=10)

        # ABOUT
        ab = tabs["About"]
        tk.Label(ab, text="0W07", bg="#c0c0c0", fg="#c85fa0",
                 font=("MS Sans Serif", 18, "bold")).pack(pady=(20, 0))
        tk.Label(ab, text="by owlito", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack()
        tk.Label(ab, text="est. 2007", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack()
        tk.Label(ab, text="A retro Windows desktop built in Python + Tkinter.",
                 bg="#c0c0c0", font=("MS Sans Serif", 8)).pack(pady=(16, 0))
        tk.Label(ab, text=f"Python {platform.python_version()}  |  "
                          f"{platform.system()} {platform.release()}",
                 bg="#c0c0c0", font=("MS Sans Serif", 7)).pack(pady=(4, 0))
        tk.Label(ab, text=f"Pillow: {'installed' if HAS_PIL else 'not installed'}",
                 bg="#c0c0c0", font=("MS Sans Serif", 7)).pack()
        tk.Label(ab, text=f"pygame: {'installed' if HAS_PYGAME else 'not installed'}",
                 bg="#c0c0c0", font=("MS Sans Serif", 7)).pack()
        tk.Label(ab, text=f"Installed apps: {len(STATE.installed_apps)}",
                 bg="#c0c0c0", font=("MS Sans Serif", 7)).pack()

        show(tab_name)

    # ---------- Other dialogs ----------
    def open_documents(self):
        win = RetroWindow(self.root, title="My Documents", width=380, height=260, desktop=self)
        tk.Label(win.content, text="No documents yet.", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(pady=20)
    def open_find(self):
        win = RetroWindow(self.root, title="Find", width=380, height=150, desktop=self)
        tk.Label(win.content, text="Find what:", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(anchor="w", padx=6, pady=(6, 0))
        tk.Entry(win.content, font=("MS Sans Serif", 8)).pack(fill="x", padx=6)
        tk.Button(win.content, text="Find Now",
                  font=("MS Sans Serif", 8)).pack(pady=6)
    def open_help(self):
        win = RetroWindow(self.root, title="About 0W07", width=320, height=180, desktop=self)
        tk.Label(win.content, text="0W07", bg="#c0c0c0", fg="#c85fa0",
                 font=("MS Sans Serif", 14, "bold")).pack(pady=(14, 0))
        tk.Label(win.content, text="made by owlito", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack()
        tk.Label(win.content, text="est. 2007", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack()
    def open_run(self):
        win = RetroWindow(self.root, title="Run", width=380, height=150, desktop=self)
        tk.Label(win.content, text="Type the name of a program:",
                 bg="#c0c0c0", font=("MS Sans Serif", 8)).pack(anchor="w", padx=6, pady=(6, 0))
        entry = tk.Entry(win.content, font=("MS Sans Serif", 8))
        entry.pack(fill="x", padx=6); entry.focus_set()
        def go():
            cmd = entry.get().strip().lower()
            table = {
                "notepad": self.open_notepad, "notepad.exe": self.open_notepad,
                "calc": self.open_calculator, "calculator": self.open_calculator,
                "paint": self.open_paint, "mspaint": self.open_paint,
                "cmd": self.open_cmd, "command": self.open_cmd,
                "music": self.open_music_player, "player": self.open_music_player,
                "store": self.open_store, "shop": self.open_store,
                "snake": self.open_snake, "pong": self.open_pong,
                "tetris": self.open_tetris, "clock": self.open_clock, "dice": self.open_dice,
                "explorer": self.open_file_explorer, "files": self.open_file_explorer,
                "settings": self.open_settings, "control": self.open_settings,
            }
            if cmd in table: table[cmd]()
            elif cmd in ("shutdown", "shut down"): self.open_shutdown()
            else: SOUNDS.error()
            win.destroy()
        row = tk.Frame(win.content, bg="#c0c0c0"); row.pack(pady=6)
        tk.Button(row, text="OK", width=8, font=("MS Sans Serif", 8),
                  command=go).pack(side="left", padx=2)
        tk.Button(row, text="Cancel", width=8, font=("MS Sans Serif", 8),
                  command=win.destroy).pack(side="left", padx=2)
        entry.bind("<Return>", lambda e: go())
    def open_shutdown(self):
        win = RetroWindow(self.root, title="Shut Down 0W07", width=340, height=160, desktop=self)
        tk.Label(win.content, text="Are you sure you want to shut down 0W07?",
                 bg="#c0c0c0", font=("MS Sans Serif", 8),
                 wraplength=300).pack(pady=14)
        row = tk.Frame(win.content, bg="#c0c0c0"); row.pack()
        def do_shutdown():
            SOUNDS.shutdown(); win.destroy()
            persist_state()
            self.root.after(900, lambda: ShutdownScreen(self.root))
        tk.Button(row, text="Yes", width=8, font=("MS Sans Serif", 8),
                  command=do_shutdown).pack(side="left", padx=2)
        tk.Button(row, text="No", width=8, font=("MS Sans Serif", 8),
                  command=win.destroy).pack(side="left", padx=2)


if __name__ == "__main__":
    OW07Desktop()
    try: tk.mainloop()
    except Exception: pass