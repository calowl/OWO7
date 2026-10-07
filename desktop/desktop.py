"""OW07Desktop — the main desktop class that ties everything together."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from core.state import STATE, persist_state
from core.sounds import SOUNDS
from core.retro_window import RetroWindow

from screens.boot import BootScreen
from screens.login import LoginScreen
from screens.shutdown import ShutdownScreen

from desktop.mascots import MascotManager
from desktop.icons import IconGrid
from desktop.taskbar import Taskbar
from desktop.start_menu import StartMenu

from apps.tetris import TetrisWindow
from apps.clock import ClockWindow
from apps.dice import DiceWindow
from apps.snake import SnakeWindow
from apps.pong import PongWindow
from apps.paint import PaintWindow
from apps.notepad import NotepadWindow
from apps.cmd import CommandPromptWindow
from apps.music_player import MusicPlayerWindow
from apps.file_explorer import FileExplorerWindow
from apps.calculator import CalculatorWindow
from apps.store import StoreWindow, STORE_APPS, get_store_app

try:
    import doom
    HAS_DOOM = True
except Exception as e:
    print("[desktop] doom not available:", e)
    HAS_DOOM = False


class OW07Desktop:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("0W07")
        self.root.configure(bg=STATE.desktop_color)

        self.fullscreen = True
        try:
            self.root.attributes("-fullscreen", True)
        except Exception:
            self.root.geometry("1024x720")

        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.windows = []
        self.wallpaper_label = None
        self.settings_win = None
        self.login_screen = None
        self.boot_screen = None

        self.apply_wallpaper()
        self.mascots = MascotManager(self.root)
        self.icons = IconGrid(self.root, self)
        self.taskbar = Taskbar(self.root, self)
        self.start_menu = StartMenu(self.root, self)
        self.start_menu.desktop = self  # backwards-compat

        # Desktop background right-click menu
        self.desktop_menu = None
        self.root.bind("<Button-3>", self.show_desktop_menu)
        self.root.bind("<Button-1>", self.deselect_icons, add="+")

        self.icons.build()
        self.taskbar.start_clock()

        if STATE.mascots_enabled:
            self.mascots.spawn(STATE.mascot_count)

        self.start_flow()

    # ==================================================================
    #  Boot → Login → Desktop
    # ==================================================================
    def start_flow(self):
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

    # ==================================================================
    #  Fullscreen
    # ==================================================================
    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        try:
            self.root.attributes("-fullscreen", self.fullscreen)
        except Exception:
            pass

    def exit_fullscreen(self, event=None):
        if self.fullscreen:
            self.fullscreen = False
            try:
                self.root.attributes("-fullscreen", False)
            except Exception:
                pass

    # ==================================================================
    #  Wallpaper
    # ==================================================================
    def apply_wallpaper(self):
        if self.wallpaper_label:
            try:
                self.wallpaper_label.destroy()
            except Exception:
                pass
            self.wallpaper_label = None

        if not STATE.wallpaper_path or not os.path.isfile(STATE.wallpaper_path):
            return

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        try:
            if HAS_PIL:
                img = Image.open(STATE.wallpaper_path)
                img = img.resize((sw, sh), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
            else:
                photo = tk.PhotoImage(file=STATE.wallpaper_path)
        except Exception as e:
            print("wallpaper failed:", e)
            return

        lbl = tk.Label(self.root, image=photo, bd=0, bg=STATE.desktop_color)
        lbl.image = photo
        lbl.place(x=0, y=0, width=sw, height=sh)
        lbl.lower()
        self.wallpaper_label = lbl

    # ==================================================================
    #  Desktop icons
    # ==================================================================
    def refresh_desktop(self):
        self.icons.build()
        if STATE.mascots_enabled:
            self.mascots.spawn(STATE.mascot_count)

    def deselect_icons(self, event=None):
        self.icons.deselect(event)

    def recolor_icons(self, color):
        self.icons.recolor(color)

    # ==================================================================
    #  Desktop right-click menu
    # ==================================================================
    def show_desktop_menu(self, event):
        self.close_desktop_menu()
        m = tk.Toplevel(self.root)
        m.overrideredirect(True)
        m.geometry(f"+{event.x_root}+{event.y_root}")
        m.configure(bg="#ffd6e8", relief="raised", bd=2)
        self.desktop_menu = m

        def add(label, cmd):
            tk.Button(m, text=label, anchor="w",
                      bg="#ffd6e8", fg="#7a2050",
                      relief="flat", activebackground="#ffb3d9",
                      font=("MS Sans Serif", 8),
                      command=lambda: (self.close_desktop_menu(), cmd())
                      ).pack(fill="x", padx=2, pady=1)

        add("♥ Refresh", self.refresh_desktop)
        add("🌸 Change background", self.pick_wallpaper)
        add("✨ Desktop colour...",
            lambda: self.open_settings_tab("Appearance"))
        add("🛍 Open Store", self.open_store)

    def close_desktop_menu(self):
        if self.desktop_menu:
            try:
                self.desktop_menu.destroy()
            except Exception:
                pass
            self.desktop_menu = None

    def pick_wallpaper(self):
        p = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.gif *.jpg *.jpeg"),
                       ("All", "*.*")])
        if p:
            STATE.wallpaper_path = p
            self.apply_wallpaper()
            persist_state()

    # ==================================================================
    #  Window registry (called by RetroWindow)
    # ==================================================================
    def register_window(self, win, title):
        self.windows.append(win)
        self.taskbar.add_window_button(win, title)

    def unregister_window(self, win):
        if win in self.windows:
            self.windows.remove(win)
        self.taskbar.remove_window_button(win)

    def set_taskbar_state(self, win, minimized=False):
        self.taskbar.set_button_state(win, minimized=minimized)

    def highlight_taskbar(self, win):
        self.taskbar.highlight(win)

    def update_window_title(self, win, title):
        self.taskbar.update_button_text(win, title)

    # ==================================================================
    #  Start menu passthrough
    # ==================================================================
    def toggle_start_menu(self):
        self.start_menu.toggle()

    # ==================================================================
    #  App launchers
    # ==================================================================
    def open_music_player(self):   MusicPlayerWindow(self.root, desktop=self)
    def open_notepad(self):        NotepadWindow(self.root, desktop=self)
    def open_paint(self):          PaintWindow(self.root, desktop=self)
    def open_cmd(self):            CommandPromptWindow(self.root, desktop=self)
    def open_snake(self):          SnakeWindow(self.root, desktop=self)
    def open_pong(self):           PongWindow(self.root, desktop=self)
    def open_file_explorer(self):  FileExplorerWindow(self.root, desktop=self)
    def open_tetris(self):         TetrisWindow(self.root, desktop=self)
    def open_clock(self):          ClockWindow(self.root, desktop=self)
    def open_dice(self):           DiceWindow(self.root, desktop=self)
    def open_calculator(self):     CalculatorWindow(self.root, desktop=self)
    def open_store(self):          StoreWindow(self.root, desktop=self)

    def open_doom(self):
        if not HAS_DOOM:
            SOUNDS.error()
            messagebox.showerror("Doom", "doom.py is not available.")
            return
        doom.DoomWindow(self.root, desktop=self)

    def open_recycle(self):
        win = RetroWindow(self.root, title="Recycle Bin",
                          width=380, height=260, desktop=self)
        tk.Label(win.content, text="🗑  Recycle Bin is empty.",
                 bg="#c0c0c0", font=("MS Sans Serif", 10)).pack(pady=40)

    # ==================================================================
    #  Settings (implemented in Step 5)
    # ==================================================================
    def open_settings(self):
        self.open_settings_tab("Appearance")

    def open_settings_tab(self, tab_name):
        from settings.settings_window import SettingsWindow
        if self.settings_win and self.settings_win.winfo_exists():
            self.settings_win.lift()
            self.settings_win.show_tab(tab_name)
            return
        self.settings_win = SettingsWindow(self.root, desktop=self,
                                           initial_tab=tab_name)
        self.settings_win.on_close = lambda: setattr(self, "settings_win", None)

    # ==================================================================
    #  Start menu dialogs
    # ==================================================================
    def open_documents(self):
        win = RetroWindow(self.root, title="My Documents",
                          width=380, height=260, desktop=self)
        tk.Label(win.content, text="No documents yet.", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(pady=20)

    def open_find(self):
        win = RetroWindow(self.root, title="Find",
                          width=380, height=150, desktop=self)
        tk.Label(win.content, text="Find what:", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(anchor="w", padx=6, pady=(6, 0))
        tk.Entry(win.content, font=("MS Sans Serif", 8)).pack(fill="x", padx=6)
        tk.Button(win.content, text="Find Now",
                  font=("MS Sans Serif", 8)).pack(pady=6)

    def open_help(self):
        win = RetroWindow(self.root, title="About 0W07",
                          width=320, height=180, desktop=self)
        tk.Label(win.content, text="0W07", bg="#c0c0c0", fg="#c85fa0",
                 font=("MS Sans Serif", 14, "bold")).pack(pady=(14, 0))
        tk.Label(win.content, text="made by owlito", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack()
        tk.Label(win.content, text="est. 2007", bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack()

    def open_run(self):
        win = RetroWindow(self.root, title="Run",
                          width=380, height=150, desktop=self)
        tk.Label(win.content, text="Type the name of a program:",
                 bg="#c0c0c0",
                 font=("MS Sans Serif", 8)).pack(anchor="w", padx=6, pady=(6, 0))
        entry = tk.Entry(win.content, font=("MS Sans Serif", 8))
        entry.pack(fill="x", padx=6)
        entry.focus_set()

        def go():
            cmd = entry.get().strip().lower()
            table = {
                "notepad": self.open_notepad, "notepad.exe": self.open_notepad,
                "calc": self.open_calculator, "calculator": self.open_calculator,
                "paint": self.open_paint, "mspaint": self.open_paint,
                "cmd": self.open_cmd, "command": self.open_cmd,
                "music": self.open_music_player,
                "player": self.open_music_player,
                "store": self.open_store, "shop": self.open_store,
                "snake": self.open_snake, "pong": self.open_pong,
                "doom": self.open_doom, "tetris": self.open_tetris,
                "clock": self.open_clock, "dice": self.open_dice,
                "explorer": self.open_file_explorer,
                "files": self.open_file_explorer,
                "settings": self.open_settings, "control": self.open_settings,
            }
            if cmd in table:
                table[cmd]()
            elif cmd in ("shutdown", "shut down"):
                self.open_shutdown()
            else:
                SOUNDS.error()
            win.destroy()

        row = tk.Frame(win.content, bg="#c0c0c0")
        row.pack(pady=6)
        tk.Button(row, text="OK", width=8, font=("MS Sans Serif", 8),
                  command=go).pack(side="left", padx=2)
        tk.Button(row, text="Cancel", width=8, font=("MS Sans Serif", 8),
                  command=win.destroy).pack(side="left", padx=2)
        entry.bind("<Return>", lambda e: go())

    def open_shutdown(self):
        win = RetroWindow(self.root, title="Shut Down 0W07",
                          width=340, height=160, desktop=self)
        tk.Label(win.content,
                 text="Are you sure you want to shut down 0W07?",
                 bg="#c0c0c0", font=("MS Sans Serif", 8),
                 wraplength=300).pack(pady=14)
        row = tk.Frame(win.content, bg="#c0c0c0")
        row.pack()

        def do_shutdown():
            SOUNDS.shutdown()
            win.destroy()
            persist_state()
            self.root.after(900, lambda: ShutdownScreen(self.root))

        tk.Button(row, text="Yes", width=8, font=("MS Sans Serif", 8),
                  command=do_shutdown).pack(side="left", padx=2)
        tk.Button(row, text="No", width=8, font=("MS Sans Serif", 8),
                  command=win.destroy).pack(side="left", padx=2)