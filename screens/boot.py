"""Boot splash screen shown at startup."""
import os
import tkinter as tk

from core.state import ASSETS_DIR
from core.sounds import SOUNDS

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


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
        except Exception as e:
            print("[boot] startup sound failed:", e)

        container = tk.Frame(self.splash, bg="#000000")
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text="0W07", bg="#000000", fg="#ffb3d9",
                 font=("MS Sans Serif", 72, "bold")).pack()
        tk.Label(container, text="version 0.6   |   owlito   |   est. 2007",
                 bg="#000000", fg="#008080",
                 font=("MS Sans Serif", 10)).pack(pady=(0, 24))

        # Optional boot image
        self._image_ref = None
        try:
            img = self._load_boot_image()
            if img is not None:
                self._image_ref = img
                tk.Label(container, image=img, bg="#000000").pack(pady=(0, 24))
        except Exception as e:
            print("[boot] image failed:", e)

        # Progress bar
        bar_wrap = tk.Frame(container, bg="#000000")
        bar_wrap.pack()
        self.bar_bg = tk.Frame(bar_wrap, bg="#2a2a2a", width=420, height=20,
                               relief="sunken", bd=2)
        self.bar_bg.pack()
        self.bar_bg.pack_propagate(False)
        self.bar_fill = tk.Frame(self.bar_bg, bg="#ff69b4")
        self.bar_fill.place(x=0, y=0, width=0, height=16)

        self.status = tk.Label(container, text="Starting 0W07...",
                               bg="#000000", fg="#ffb3d9",
                               font=("MS Sans Serif", 8))
        self.status.pack(pady=(8, 0))
        tk.Label(container, text="press ESC to skip", bg="#000000",
                 fg="#804060", font=("MS Sans Serif", 7)).pack(pady=(16, 0))

        self.steps = 70
        self.current = 0
        self.bar_target = 416
        self.messages = [
            (0.00, "Starting 0W07..."),
            (0.15, "Loading kernel..."),
            (0.35, "Mounting file system..."),
            (0.55, "Loading apps..."),
            (0.75, "Waking up the desktop..."),
            (0.90, "Almost there..."),
        ]
        self.splash.bind("<Escape>", lambda e: self.finish())
        self.splash.bind("<Return>", lambda e: self.finish())
        self.splash.after(100, self._tick)

    # --------------------------------------------------------------
    def _grab_focus(self):
        try:
            self.splash.focus_force()
        except Exception:
            pass

    def _load_boot_image(self):
        for name in ["boot.png", "boot.gif", "boot.jpg", "boot.jpeg",
                     "startup.png", "startup.gif"]:
            path = os.path.join(ASSETS_DIR, name)
            if not os.path.isfile(path):
                continue
            ext = name.lower().rsplit(".", 1)[-1]
            if ext in ("jpg", "jpeg"):
                if HAS_PIL:
                    try:
                        img = Image.open(path)
                        img.thumbnail((360, 360))
                        return ImageTk.PhotoImage(img)
                    except Exception as e:
                        print("[boot] bad image:", e)
            else:
                try:
                    return tk.PhotoImage(file=path)
                except Exception as e:
                    print("[boot] bad image:", e)
        return None

    def _tick(self):
        if self.finished:
            return
        if self.current >= self.steps:
            try:
                self.status.config(text="Welcome.")
            except Exception:
                pass
            self.splash.after(400, self.finish)
            return

        self.current += 1
        pct = self.current / self.steps

        try:
            self.bar_fill.place(x=0, y=0,
                                width=int(self.bar_target * pct), height=16)
            for t, m in reversed(self.messages):
                if pct >= t:
                    self.status.config(text=m)
                    break
        except Exception as e:
            print("[boot] tick failed:", e)

        self.splash.after(50, self._tick)

    def finish(self):
        if self.finished:
            return
        self.finished = True
        try:
            self.splash.destroy()
        except Exception:
            pass
        try:
            self.on_done()
        except Exception as e:
            print("[boot] handoff failed:", e)
            try:
                self.root.deiconify()
            except Exception:
                pass