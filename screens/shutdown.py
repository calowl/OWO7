"""Shutdown screen shown when the user shuts down 0W07."""
import os
import sys
import time
import tkinter as tk


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

        # Hide the desktop, close any open windows
        try:
            root.withdraw()
        except Exception:
            pass
        for w in list(root.winfo_children()):
            if isinstance(w, tk.Toplevel):
                try:
                    w.destroy()
                except Exception:
                    pass

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
        try:
            self.win.destroy()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        time.sleep(0.2)
        os.execl(sys.executable, sys.executable, *sys.argv)

    def turn_off(self):
        try:
            self.root.destroy()
        except Exception:
            pass