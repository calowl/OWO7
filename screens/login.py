"""Login screen shown after the boot splash."""
import tkinter as tk

from core.state import STATE
from core.sounds import SOUNDS


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
        try:
            self.pw_entry.focus_force()
        except Exception:
            pass

    def try_login(self):
        SOUNDS.click()
        STATE.username = STATE.username or "owlito"
        try:
            self.win.destroy()
        except Exception:
            pass
        self.on_login()

    def shutdown(self):
        try:
            self.win.destroy()
        except Exception:
            pass
        self.on_shutdown()