"""Global state + config persistence for 0W07."""
import json
import os

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
# core/ lives inside the project root, so go up one level to reach assets/
CORE_DIR    = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(CORE_DIR)
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
MASCOTS_DIR = os.path.join(ASSETS_DIR, "mascots")
SOUNDS_DIR  = os.path.join(ASSETS_DIR, "sounds")
WALLS_DIR   = os.path.join(ASSETS_DIR, "wallpapers")
MUSIC_DIR   = os.path.join(ASSETS_DIR, "music")
SFX_DIR     = os.path.join(MUSIC_DIR, "sfx")
CONFIG_PATH = os.path.join(ASSETS_DIR, "config.json")

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------
TASKBAR_H = 32


# ------------------------------------------------------------------
# State container
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# Config persistence
# ------------------------------------------------------------------
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


def _apply_config():
    """Read config.json and copy values into STATE. Runs on import."""
    cfg = load_config()
    STATE.text_scale      = cfg.get("text_scale", 1.0)
    STATE.desktop_color   = cfg.get("desktop_color", "#008080")
    STATE.mascots_enabled = cfg.get("mascots_enabled", False)
    STATE.mascot_count    = cfg.get("mascot_count", 3)
    STATE.show_clock      = cfg.get("show_clock", True)
    STATE.wallpaper_path  = cfg.get("wallpaper_path")
    STATE.installed_apps  = set(cfg.get("installed_apps", []))
    STATE.username        = cfg.get("username", "owlito")


def persist_state():
    """Write current STATE to config.json."""
    save_config({
        "text_scale":      STATE.text_scale,
        "desktop_color":   STATE.desktop_color,
        "mascots_enabled": STATE.mascots_enabled,
        "mascot_count":    STATE.mascot_count,
        "show_clock":      STATE.show_clock,
        "wallpaper_path":  STATE.wallpaper_path,
        "installed_apps":  sorted(STATE.installed_apps),
        "username":        STATE.username,
    })


# Load saved values immediately when this module is imported
_apply_config()