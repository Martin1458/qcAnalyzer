import sys
import tkinter as tk
import multiprocessing
from pathlib import Path

from gui.app_window import AppWindow

BASE_DIR = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    root.title("Rocket League Quick Chat Analyzer")
    root.geometry("1100x780")
    root.minsize(900, 620)

    icon_path = BASE_DIR / "icon.ico"
    if icon_path.exists():
        root.iconbitmap(str(icon_path))

    app = AppWindow(root, BASE_DIR)
    app.pack(fill=tk.BOTH, expand=True)

    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
