"""Music player."""
import os
import random
import time
import tkinter as tk

from core.retro_window import RetroWindow
from core.state import MUSIC_DIR
from core.sounds import SOUNDS, HAS_PYGAME

try:
    import pygame
except ImportError:
    pygame = None


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
        self.volume = tk.Scale(vol_frame, from_=0, to=100,
                               orient="horizontal", showvalue=False,
                               bg="#c0c0c0", bd=1, highlightthickness=0,
                               length=200, troughcolor="#ffd6e8",
                               activebackground="#ffb3d9",
                               command=self.set_volume)
        self.volume.set(70)
        self.volume.pack(side="left", fill="x", expand=True, padx=6)

        opts = tk.Frame(self.content, bg="#c0c0c0")
        opts.pack(fill="x", padx=6)
        self.shuffle_var = tk.BooleanVar(value=False)
        self.loop_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opts, text="Shuffle", variable=self.shuffle_var,
                       bg="#c0c0c0", fg="#7a2050",
                       activebackground="#c0c0c0", selectcolor="#ffd6e8",
                       font=("MS Sans Serif", 8)).pack(side="left")
        tk.Checkbutton(opts, text="Loop", variable=self.loop_var,
                       bg="#c0c0c0", fg="#7a2050",
                       activebackground="#c0c0c0", selectcolor="#ffd6e8",
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
                                      font=("MS Sans Serif", 8),
                                      activestyle="none",
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
                                   font=("MS Sans Serif", 9),
                                   activestyle="none", bd=0,
                                   selectbackground="#ffb3d9",
                                   selectforeground="#7a2050",
                                   highlightthickness=0)
        self.playlist.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(pl_inner, command=self.playlist.yview)
        sb.pack(side="right", fill="y")
        self.playlist.config(yscrollcommand=sb.set)
        self.playlist.bind("<Double-Button-1>", self.play_selected)

        self.status_lbl = tk.Label(self.content, text="", bg="#c0c0c0",
                                   fg="#7a2050",
                                   font=("MS Sans Serif", 7), anchor="w")
        self.status_lbl.pack(fill="x", padx=6, pady=(0, 4))

        self.library = {"All": []}
        self.folder_order = ["All"]
        self.current_folder = "All"
        self.view_tracks = []
        self.current_index = -1
        self.playing = False
        self.paused = False
        self.elapsed = 0.0
        self.duration = 0.0
        self.last_tick = time.time()

        if not HAS_PYGAME:
            self.status_lbl.config(
                text="pygame not installed. Run: pip install pygame")

        self.scan_library()
        self.refresh_folder_list()
        self.select_folder("All")
        self.after(100, self.tick)

    def scan_library(self):
        self.library = {"All": []}
        if not os.path.isdir(MUSIC_DIR):
            return
        for root, dirs, files in os.walk(MUSIC_DIR):
            rel = os.path.relpath(root, MUSIC_DIR)
            top = None if rel == "." else rel.split(os.sep)[0]
            parts = [] if rel == "." else rel.split(os.sep)
            if any(p in self.EXCLUDED_FOLDERS for p in parts):
                dirs[:] = []
                continue
            for name in sorted(files):
                if name.lower().endswith(self.AUDIO_EXTS):
                    full = os.path.join(root, name)
                    disp = (name if rel == "."
                            else rel.replace(os.sep, " / ") + " / " + name)
                    self.library["All"].append((full, disp))
                    if top:
                        self.library.setdefault(top, []).append((full, disp))
        self.folder_order = ["All"] + sorted(k for k in self.library if k != "All")

    def refresh_folder_list(self):
        self.folder_list.delete(0, tk.END)
        for name in self.folder_order:
            self.folder_list.insert(
                tk.END, f"{name} ({len(self.library.get(name, []))})")

    def select_folder(self, name):
        if name not in self.folder_order:
            name = "All"
        self.current_folder = name
        try:
            idx = self.folder_order.index(name)
            self.folder_list.selection_clear(0, tk.END)
            self.folder_list.selection_set(idx)
            self.folder_list.activate(idx)
        except Exception:
            pass
        self.view_tracks = list(self.library.get(name, []))
        self.refresh_playlist()

    def on_folder_select(self, event=None):
        sel = self.folder_list.curselection()
        if not sel:
            return
        name = self.folder_order[sel[0]]
        if name != self.current_folder:
            self.select_folder(name)

    def refresh_playlist(self):
        self.playlist.delete(0, tk.END)
        if not self.view_tracks:
            self.playlist.insert(tk.END, " (no tracks)")
            self.playlist.itemconfig(0, foreground="#888888")
            return
        for _, disp in self.view_tracks:
            self.playlist.insert(tk.END, "♪ " + disp)
        self.status_lbl.config(
            text=f"{self.current_folder}: {len(self.view_tracks)} track(s)")

    def reload(self):
        self.scan_library()
        self.refresh_folder_list()
        self.select_folder(self.current_folder)

    def play_index(self, idx):
        if not HAS_PYGAME or not self.view_tracks:
            return
        if idx < 0 or idx >= len(self.view_tracks):
            return
        self.stop_playback()
        path, disp = self.view_tracks[idx]
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.volume.get() / 100.0)
            pygame.mixer.music.play()
        except Exception as e:
            SOUNDS.error()
            self.status_lbl.config(text=f"Error: {e}")
            return
        self.current_index = idx
        self.playing = True
        self.paused = False
        self.elapsed = 0.0
        self.last_tick = time.time()
        try:
            snd = pygame.mixer.Sound(path)
            self.duration = float(snd.get_length())
        except Exception:
            self.duration = 0.0
        self.now_playing.config(text="♪ " + disp)
        self.play_btn.config(text="❚❚")
        try:
            self.playlist.selection_clear(0, tk.END)
            self.playlist.selection_set(idx)
            self.playlist.see(idx)
        except Exception:
            pass

    def stop_playback(self):
        if HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self.playing = False
        self.paused = False

    def stop(self):
        self.stop_playback()
        self.elapsed = 0.0
        self.play_btn.config(text="▶")
        self.update_progress()

    def toggle_play(self):
        if not self.view_tracks:
            self.reload()
            if not self.view_tracks:
                SOUNDS.error()
                return
        if not self.playing:
            self.play_index(self.current_index
                            if 0 <= self.current_index < len(self.view_tracks)
                            else 0)
        elif self.paused:
            try:
                pygame.mixer.music.unpause()
                self.paused = False
                self.last_tick = time.time()
                self.play_btn.config(text="❚❚")
            except Exception:
                pass
        else:
            try:
                pygame.mixer.music.pause()
                self.paused = True
                self.play_btn.config(text="▶")
            except Exception:
                pass

    def next_track(self):
        if not self.view_tracks:
            return
        idx = (random.randrange(len(self.view_tracks))
               if self.shuffle_var.get()
               else (self.current_index + 1) % len(self.view_tracks))
        self.play_index(idx)

    def prev_track(self):
        if not self.view_tracks:
            return
        idx = (random.randrange(len(self.view_tracks))
               if self.shuffle_var.get()
               else (self.current_index - 1) % len(self.view_tracks))
        self.play_index(idx)

    def play_selected(self, event=None):
        sel = self.playlist.curselection()
        if not sel:
            return
        self.play_index(sel[0])

    def set_volume(self, val):
        if HAS_PYGAME:
            try:
                pygame.mixer.music.set_volume(float(val) / 100.0)
            except Exception:
                pass

    def seek(self, event):
        if not self.playing or self.duration <= 0 or not HAS_PYGAME:
            return
        w = self.progress_canvas.winfo_width()
        if w <= 0:
            return
        pct = max(0.0, min(1.0, event.x / w))
        try:
            pygame.mixer.music.play(start=pct * self.duration)
            self.elapsed = pct * self.duration
            self.last_tick = time.time()
            if self.paused:
                pygame.mixer.music.pause()
        except Exception:
            pass

    def update_progress(self):
        w = self.progress_canvas.winfo_width() or 400
        h = self.progress_canvas.winfo_height() or 14
        self.progress_canvas.delete("all")
        self.progress_canvas.create_rectangle(0, 0, w, h, fill="#2a2a2a",
                                              outline="")
        if self.duration > 0:
            pct = min(1.0, max(0.0, self.elapsed / self.duration))
            fill_w = int(w * pct)
            if fill_w > 0:
                self.progress_canvas.create_rectangle(
                    0, 0, fill_w, h, fill="#ff69b4", outline="")
            m1, s1 = divmod(int(self.elapsed), 60)
            m2, s2 = divmod(int(self.duration), 60)
            self.time_lbl.config(text=f"{m1}:{s1:02d} / {m2}:{s2:02d}")
        else:
            m1, s1 = divmod(int(self.elapsed), 60)
            self.time_lbl.config(text=f"{m1}:{s1:02d} / --:--")

    def tick(self):
        if not self.winfo_exists():
            return
        try:
            now = time.time()
            dt = now - self.last_tick
            self.last_tick = now
            if self.playing and not self.paused:
                self.elapsed += dt
                if HAS_PYGAME:
                    try:
                        busy = pygame.mixer.music.get_busy()
                    except Exception:
                        busy = False
                    if not busy and self.elapsed > 0.5:
                        if self.loop_var.get():
                            self.play_index(self.current_index)
                        else:
                            self.next_track()
            self.update_progress()
        except Exception as e:
            print("music tick error:", e)
        try:
            self.after(100, self.tick)
        except Exception:
            pass

    def _close(self):
        self.stop_playback()
        super()._close()