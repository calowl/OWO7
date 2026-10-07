"""Sound manager for 0W07."""
import os
import winsound

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    HAS_PYGAME = True
except Exception as _pg_err:
    HAS_PYGAME = False
    print("pygame not available:", _pg_err)

from .state import STATE, SFX_DIR, SOUNDS_DIR


class SoundManager:
    SFX_EXTS = (".wav", ".mp3", ".ogg", ".flac")

    def __init__(self):
        self._cache = {}

    def _find_path(self, name):
        if os.path.isdir(SFX_DIR):
            for ext in self.SFX_EXTS:
                p = os.path.join(SFX_DIR, name + ext)
                if os.path.isfile(p):
                    return p
        p = os.path.join(SOUNDS_DIR, name + ".wav")
        if os.path.isfile(p):
            return p
        return None

    def _play(self, name, beep_kind):
        path = self._find_path(name)
        if not path:
            try:
                winsound.MessageBeep(beep_kind)
            except Exception:
                pass
            return

        ext = path.lower().rsplit(".", 1)[-1]

        # Native wav playback without pygame
        if ext == "wav" and not HAS_PYGAME:
            try:
                winsound.PlaySound(
                    path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC,
                )
                return
            except Exception as e:
                print("winsound failed:", name, e)

        # pygame path
        if HAS_PYGAME:
            try:
                snd = self._cache.get(name)
                if snd is None or getattr(snd, "_src_path", None) != path:
                    snd = pygame.mixer.Sound(path)
                    snd._src_path = path
                    self._cache[name] = snd
                snd.stop()
                snd.play()
                return
            except Exception as e:
                print("pygame sfx failed:", name, e)

        # Fallback beep
        try:
            winsound.MessageBeep(beep_kind)
        except Exception:
            pass

    # -- Named events -------------------------------------------------
    def startup(self):
        if not (STATE.sound_enabled and STATE.startup_sound):
            return
        self._play("startup", winsound.MB_ICONASTERISK)

    def click(self):
        if not (STATE.sound_enabled and STATE.click_sounds):
            return
        self._play("click", winsound.MB_OK)

    def mascot(self):
        if not (STATE.sound_enabled and STATE.mascot_sounds):
            return
        self._play("mascot", winsound.MB_ICONASTERISK)

    def error(self):
        if not (STATE.sound_enabled and STATE.error_sounds):
            return
        self._play("error", winsound.MB_ICONHAND)

    def shutdown(self):
        if not STATE.sound_enabled:
            return
        self._play("shutdown", winsound.MB_ICONEXCLAMATION)


# Shared singleton — import this everywhere
SOUNDS = SoundManager()