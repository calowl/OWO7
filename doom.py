"""
DOOM 0W07 — a raycaster FPS for the 0W07 desktop.

Standalone:  python doom.py
From 0W07:   main.py calls install_context(SOUNDS, RetroWindow) at startup.
             This injects the OS's sound manager and window base class so
             Doom integrates with the desktop without a circular import.
"""
import math
import random
import tkinter as tk
import time
import traceback


# ============================================================
#  Injected context (defaults allow standalone use)
# ============================================================
SOUNDS = None
OW07_RETRO_WINDOW = None


class _StubSounds:
    """Fallback used when doom.py runs standalone."""
    def click(self): pass
    def error(self): pass
    def mascot(self): pass


class _StubRetro(tk.Toplevel):
    """Minimal window shell for standalone runs (no title bar buttons
    hooked into the 0W07 taskbar)."""

    def __init__(self, master, title="Window", width=300, height=200,
                 x=120, y=120, desktop=None, **kwargs):
        super().__init__(master)
        self.overrideredirect(True)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.configure(bg="#c0c0c0")
        self.desktop = desktop
        self.taskbar_btn = None
        self.minimized = False
        self.maximized = False

        self.title_bar = tk.Frame(self, bg="#c85fa0", relief="raised", bd=2)
        self.title_bar.pack(fill="x")
        tk.Label(self.title_bar, text=title, bg="#c85fa0", fg="white",
                 font=("MS Sans Serif", 8, "bold")).pack(side="left", padx=5)
        tk.Button(self.title_bar, text="X", bg="#ffd6e8", fg="#7a2050",
                  relief="raised", bd=1, width=2,
                  command=self._close).pack(side="right", padx=1, pady=1)

        self.content = tk.Frame(self, bg="#c0c0c0", relief="sunken", bd=2)
        self.content.pack(fill="both", expand=True, padx=2, pady=2)

        self.title_bar.bind("<Button-1>", self._start_move)
        self.title_bar.bind("<B1-Motion>", self._do_move)

    def _start_move(self, e):
        self._dx, self._dy = e.x, e.y

    def _do_move(self, e):
        self.geometry(
            f"+{self.winfo_x() + e.x - self._dx}"
            f"+{self.winfo_y() + e.y - self._dy}")

    def _close(self):
        self.destroy()


def install_context(sounds_module, retro_window_class):
    """Called by main.py at startup. Injects the OS's SOUNDS and
    RetroWindow so Doom integrates with the desktop."""
    global SOUNDS, OW07_RETRO_WINDOW
    SOUNDS = sounds_module
    OW07_RETRO_WINDOW = retro_window_class
    print("[doom] context installed from 0W07")


def _sounds():
    return SOUNDS if SOUNDS is not None else _StubSounds()


# ============================================================
#  Doom implementation (mixed into the injected base at runtime)
# ============================================================
class _DoomImpl:
    RES = 4
    FOV = math.pi / 3

    MAP_STR = [
        "####################",
        "#..................#",
        "#..####..####..##..#",
        "#..#..........#..#.#",
        "#..#..######..#..#.#",
        "#.....#....#.....#.#",
        "#.....#....#.......#",
        "#..#..#....#..#....#",
        "#..#..######..#..#.#",
        "#..#..........#..#.#",
        "#..####..####..##..#",
        "#..................#",
        "####################",
    ]

    ENEMY_TYPES = {
        "skull": {"emoji": "💀", "hp": 1, "speed": 0.035, "damage": 8,
                  "color": "#ffd6e8"},
        "ghost": {"emoji": "👻", "hp": 2, "speed": 0.025, "damage": 12,
                  "color": "#d4f0ff"},
        "demon": {"emoji": "👹", "hp": 3, "speed": 0.018, "damage": 18,
                  "color": "#ffd4d4"},
    }

    def __init__(self, master, desktop=None):
        super().__init__(master, title="DOOM 0W07",
                         width=700, height=560, desktop=desktop)

        self._snd = _sounds()

        self.W = 640
        self.H = 400
        self.num_rays = self.W // self.RES
        self.half_fov = self.FOV / 2

        self.map = [list(row) for row in self.MAP_STR]
        self.map_w = len(self.map[0])
        self.map_h = len(self.map)

        # Player state
        self.px = 2.5
        self.py = 2.5
        self.pa = 0.0

        self.keys = set()
        self.health = 100
        self.score = 0
        self.ammo = 30
        self.max_ammo = 30
        self.game_over = False
        self.won = False
        self.shoot_cooldown = 0
        self.hurt_flash = 0

        self.enemies = []
        self.spawn_enemies()

        # ---------- UI ----------
        self.canvas = tk.Canvas(self.content, width=self.W, height=self.H,
                                bg="black", highlightthickness=0, bd=0)
        self.canvas.pack(padx=4, pady=(4, 2))

        bar = tk.Frame(self.content, bg="#c0c0c0")
        bar.pack(fill="x", padx=4, pady=(0, 4))
        tk.Label(bar, text="WASD move · ← → turn · click to shoot",
                 bg="#c0c0c0", fg="#7a2050",
                 font=("MS Sans Serif", 8)).pack(side="left")
        tk.Button(bar, text="New Game", font=("MS Sans Serif", 8),
                  command=self.reset).pack(side="right")

        # ---------- Input ----------
        self.bind("<Key>", self.on_key)
        self.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self._canvas_click)
        self.bind("<Button-1>", lambda e: self.focus_force(), add="+")

        self.after(120, self._grab_focus)

        self._job = None
        self._last_time = None
        self.tick()

    def _grab_focus(self):
        try:
            self.focus_force()
            self.lift()
        except Exception:
            pass

    def _canvas_click(self, event):
        self.focus_force()
        self.shoot()

    # ============================================================
    #  Game state
    # ============================================================
    def reset(self):
        self.px, self.py, self.pa = 2.5, 2.5, 0.0
        self.health = 100
        self.score = 0
        self.ammo = 30
        self.game_over = False
        self.won = False
        self.hurt_flash = 0
        self.spawn_enemies()

    def spawn_enemies(self):
        self.enemies = []
        positions = [
            (8, 3, "skull"), (14, 3, "ghost"),
            (5, 8, "demon"), (15, 8, "skull"),
            (10, 5, "ghost"), (10, 9, "demon"),
        ]
        for x, y, kind in positions:
            self.enemies.append({
                "x": x + 0.5, "y": y + 0.5,
                "kind": kind,
                "hp": self.ENEMY_TYPES[kind]["hp"],
                "alive": True,
                "attack_cd": 0,
                "hit_flash": 0,
            })

    # ============================================================
    #  Input
    # ============================================================
    def on_key(self, event):
        self.keys.add(event.keysym.lower())
        return "break"

    def on_key_release(self, event):
        self.keys.discard(event.keysym.lower())

    def shoot(self):
        if self.game_over or self.won:
            return
        if self.shoot_cooldown > 0:
            return
        if self.ammo < 1:
            self._snd.error()
            return

        self.shoot_cooldown = 0.25
        self.ammo -= 1
        self._snd.click()

        best, best_d = None, 1e9
        for e in self.enemies:
            if not e["alive"]:
                continue
            ex, ey = e["x"] - self.px, e["y"] - self.py
            d = math.hypot(ex, ey)
            if d > 12:
                continue
            diff = (math.atan2(ey, ex) - self.pa + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) > 0.3:
                continue
            if self.has_los(self.px, self.py, e["x"], e["y"]) and d < best_d:
                best, best_d = e, d

        if best:
            best["hp"] -= 1
            best["hit_flash"] = 0.2
            if best["hp"] <= 0:
                best["alive"] = False
                self.score += 100
                self._snd.mascot()

    # ============================================================
    #  Raycasting helpers
    # ============================================================
    def has_los(self, x0, y0, x1, y1):
        steps = int(math.hypot(x1 - x0, y1 - y0) * 10)
        if steps < 1:
            return True
        dx, dy = (x1 - x0) / steps, (y1 - y0) / steps
        for i in range(1, steps):
            if self.is_wall(int(x0 + dx * i), int(y0 + dy * i)):
                return False
        return True

    def is_wall(self, mx, my):
        if mx < 0 or mx >= self.map_w or my < 0 or my >= self.map_h:
            return True
        return self.map[my][mx] == "#"

    def cast_ray(self, ox, oy, angle):
        dx, dy = math.cos(angle), math.sin(angle)
        map_x, map_y = int(ox), int(oy)
        ddx = abs(1 / dx) if abs(dx) > 1e-9 else 1e9
        ddy = abs(1 / dy) if abs(dy) > 1e-9 else 1e9
        if dx < 0:
            step_x = -1
            sdx = (ox - map_x) * ddx
        else:
            step_x = 1
            sdx = (map_x + 1 - ox) * ddx
        if dy < 0:
            step_y = -1
            sdy = (oy - map_y) * ddy
        else:
            step_y = 1
            sdy = (map_y + 1 - oy) * ddy
        side = 0
        for _ in range(200):
            if sdx < sdy:
                sdx += ddx
                map_x += step_x
                side = 0
            else:
                sdy += ddy
                map_y += step_y
                side = 1
            if self.is_wall(map_x, map_y):
                dist = (sdx - ddx) if side == 0 else (sdy - ddy)
                return max(0.01, dist), side
        return 100.0, 0

    # ============================================================
    #  Main loop
    # ============================================================
    def tick(self):
        if not self.winfo_exists():
            return
        try:
            now = time.time()
            if self._last_time is None:
                dt = 1 / 30.0
            else:
                dt = min(0.1, now - self._last_time)
            self._last_time = now

            if not self.game_over and not self.won:
                self.update(dt)
            self.render()

            if not self.won and not self.game_over:
                if all(not e["alive"] for e in self.enemies):
                    self.won = True
                    self._snd.mascot()
        except Exception as e:
            print("doom tick error:", e)
            traceback.print_exc()

        try:
            self._job = self.after(33, self.tick)
        except Exception:
            pass

    def update(self, dt):
        # Movement
        speed = 3.0 * dt
        rot = 2.2 * dt
        fx, fy = math.cos(self.pa), math.sin(self.pa)
        rx, ry = -fy, fx
        mvx = mvy = 0.0
        if "w" in self.keys or "up" in self.keys:
            mvx += fx * speed; mvy += fy * speed
        if "s" in self.keys or "down" in self.keys:
            mvx -= fx * speed; mvy -= fy * speed
        if "a" in self.keys:
            mvx -= rx * speed; mvy -= ry * speed
        if "d" in self.keys:
            mvx += rx * speed; mvy += ry * speed
        if "left" in self.keys:
            self.pa -= rot
        if "right" in self.keys:
            self.pa += rot

        # Wall-sliding movement
        nx, ny = self.px + mvx, self.py + mvy
        if not self.is_wall(int(nx), int(self.py)):
            self.px = nx
        if not self.is_wall(int(self.px), int(ny)):
            self.py = ny

        # Timers
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        if self.hurt_flash > 0:
            self.hurt_flash -= dt
        self.ammo = min(self.max_ammo, self.ammo + 0.6 * dt)

        # Enemies
        for e in self.enemies:
            if not e["alive"]:
                continue
            if e["hit_flash"] > 0:
                e["hit_flash"] -= dt
            if e["attack_cd"] > 0:
                e["attack_cd"] -= dt

            kind = self.ENEMY_TYPES[e["kind"]]
            ex, ey = self.px - e["x"], self.py - e["y"]
            d = math.hypot(ex, ey)
            if 1.2 < d < 10:
                step = kind["speed"] * 60 * dt
                nx = e["x"] + (ex / d) * step
                ny = e["y"] + (ey / d) * step
                if not self.is_wall(int(nx), int(e["y"])):
                    e["x"] = nx
                if not self.is_wall(int(e["x"]), int(ny)):
                    e["y"] = ny

            if d < 1.5 and e["attack_cd"] <= 0:
                self.health -= kind["damage"]
                self.hurt_flash = 0.3
                e["attack_cd"] = 1.0
                self._snd.error()
                if self.health <= 0:
                    self.health = 0
                    self.game_over = True

    # ============================================================
    #  Rendering
    # ============================================================
    def render(self):
        c = self.canvas
        c.delete("all")

        # Ceiling + floor
        c.create_rectangle(0, 0, self.W, self.H // 2,
                           fill="#2a0a1a", outline="")
        c.create_rectangle(0, self.H // 2, self.W, self.H,
                           fill="#1a0810", outline="")

        # Walls
        self.depth_buffer = [1e9] * self.num_rays
        for ray_i in range(self.num_rays):
            ray_angle = self.pa - self.half_fov + (ray_i / self.num_rays) * self.FOV
            dist, side = self.cast_ray(self.px, self.py, ray_angle)
            corrected = max(0.01, dist * math.cos(ray_angle - self.pa))
            self.depth_buffer[ray_i] = corrected

            wall_h = int(self.H / corrected)
            top = self.H // 2 - wall_h // 2
            bot = self.H // 2 + wall_h // 2
            base = 120 if side == 0 else 180
            shade = max(20, min(255, base - int(corrected * 8)))
            color = f"#{shade:02x}{shade // 3:02x}{shade // 2:02x}"
            c.create_rectangle(ray_i * self.RES, top,
                               (ray_i + 1) * self.RES, bot,
                               fill=color, outline="")

        # Enemies — sorted back to front
        visible = [e for e in self.enemies if e["alive"]]
        for e in visible:
            ex, ey = e["x"] - self.px, e["y"] - self.py
            e["_dist"] = math.hypot(ex, ey)
            e["_angle"] = math.atan2(ey, ex)
        visible.sort(key=lambda e: -e["_dist"])

        for e in visible:
            rel = (e["_angle"] - self.pa + math.pi) % (2 * math.pi) - math.pi
            if abs(rel) > self.half_fov + 0.2:
                continue
            if not self.has_los(self.px, self.py, e["x"], e["y"]):
                continue

            sx = self.W // 2 + int((rel / self.half_fov) * (self.W // 2))
            size = int(self.H / e["_dist"] * 0.6)
            if size < 4:
                continue
            sy = self.H // 2
            ri = max(0, min(self.num_rays - 1, sx // self.RES))
            if self.depth_buffer[ri] < e["_dist"] - 0.3:
                continue

            kind = self.ENEMY_TYPES[e["kind"]]
            body = "#ffffff" if e.get("hit_flash", 0) > 0 else kind["color"]
            c.create_oval(sx - size // 2, sy - size // 2,
                          sx + size // 2, sy + size // 2,
                          fill=body, outline="#c85fa0",
                          width=max(1, size // 20))
            c.create_text(sx, sy, text=kind["emoji"],
                          font=("Segoe UI Emoji", max(8, int(size * 0.7))))

        # HUD
        hb_w, hb_h, hb_x = 160, 14, 20
        hb_y = self.H - 30
        c.create_rectangle(hb_x, hb_y, hb_x + hb_w, hb_y + hb_h,
                           fill="#400000", outline="#c85fa0", width=2)
        hp_pct = max(0, self.health) / 100
        c.create_rectangle(hb_x + 2, hb_y + 2,
                           hb_x + 2 + int((hb_w - 4) * hp_pct),
                           hb_y + hb_h - 2, fill="#ff3050", outline="")
        c.create_text(hb_x + 6, hb_y + hb_h // 2, anchor="w",
                      text=f"♥ {max(0, self.health)}",
                      fill="white", font=("MS Sans Serif", 8, "bold"))
        c.create_text(self.W - 20, hb_y + hb_h // 2, anchor="e",
                      text=f"⚡ {int(self.ammo)}",
                      fill="#ffd6e8", font=("MS Sans Serif", 10, "bold"))
        c.create_text(self.W // 2, hb_y + hb_h // 2,
                      text=f"Score: {self.score}",
                      fill="#ffd6e8", font=("MS Sans Serif", 10, "bold"))

        # Crosshair
        cx, cy = self.W // 2, self.H // 2
        c.create_line(cx - 8, cy, cx + 8, cy, fill="#ff69b4", width=2)
        c.create_line(cx, cy - 8, cx, cy + 8, fill="#ff69b4", width=2)

        # Gun
        gun_y = self.H - 20
        c.create_polygon(self.W // 2 - 20, gun_y,
                         self.W // 2 + 20, gun_y,
                         self.W // 2 + 14, gun_y - 50,
                         self.W // 2 - 14, gun_y - 50,
                         fill="#404040", outline="#c85fa0", width=2)
        c.create_rectangle(self.W // 2 - 6, gun_y - 60,
                           self.W // 2 + 6, gun_y - 50,
                           fill="#606060", outline="#c85fa0")

        # Damage flash
        if self.hurt_flash > 0:
            c.create_rectangle(0, 0, self.W, self.H, fill="#ff0000",
                               outline="", stipple="gray50")

        # End screens
        if self.game_over:
            c.create_rectangle(0, self.H // 2 - 50, self.W, self.H // 2 + 50,
                               fill="#1a0810", outline="#ff3050", width=3)
            c.create_text(self.W // 2, self.H // 2 - 14, text="YOU DIED",
                          fill="#ff3050", font=("MS Sans Serif", 24, "bold"))
            c.create_text(self.W // 2, self.H // 2 + 18,
                          text=f"Score: {self.score} — Click New Game",
                          fill="white", font=("MS Sans Serif", 10))
        elif self.won:
            c.create_rectangle(0, self.H // 2 - 50, self.W, self.H // 2 + 50,
                               fill="#1a0810", outline="#ff69b4", width=3)
            c.create_text(self.W // 2, self.H // 2 - 14, text="YOU WIN!",
                          fill="#ff69b4", font=("MS Sans Serif", 24, "bold"))
            c.create_text(self.W // 2, self.H // 2 + 18,
                          text=f"Score: {self.score} — Click New Game",
                          fill="white", font=("MS Sans Serif", 10))

    # ============================================================
    #  Cleanup
    # ============================================================
    def _close(self):
        if getattr(self, "_job", None):
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        try:
            super()._close()
        except AttributeError:
            self.destroy()


# ============================================================
#  Factory — the only public entry point for opening a Doom window
# ============================================================
def DoomWindow(master, desktop=None):
    """Build and return a live Doom window."""
    base = OW07_RETRO_WINDOW if OW07_RETRO_WINDOW else _StubRetro

    # IMPORTANT: _DoomImpl must come FIRST in the bases so its __init__
    # runs. It calls super().__init__() which then hits the base window's
    # __init__ via the MRO.
    class _DoomWindow(_DoomImpl, base):
        pass

    return _DoomWindow(master, desktop=desktop)


# ============================================================
#  Standalone launcher
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("DOOM 0W07 (standalone)")
    root.geometry("760x620")

    class _FakeDesktop:
        windows = []
        def register_window(self, w, t): self.windows.append(w)
        def unregister_window(self, w):
            if w in self.windows: self.windows.remove(w)
        def set_taskbar_state(self, w, minimized=False): pass
        def highlight_taskbar(self, w): pass

    DoomWindow(root, desktop=_FakeDesktop())
    root.mainloop()