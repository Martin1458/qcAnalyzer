import tkinter as tk
from tkinter import ttk, messagebox
import json
import pathlib
import winreg

APP_NAME = "RLQCAnalyzer"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_startup_exe() -> str:
    import sys
    return sys.executable if not getattr(sys, "frozen", False) else sys.executable


def _set_startup(enabled: bool, exe_path: str):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        messagebox.showerror("Registry Error", f"Could not update startup entry:\n{e}")
        return False


def _read_startup() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


class SettingsTab(ttk.Frame):
    def __init__(self, parent, base_dir):
        super().__init__(parent)
        self._base_dir = pathlib.Path(base_dir)
        self._settings_path = self._base_dir / "settings.json"
        self._settings = self._load_settings()

        self._startup_var = tk.BooleanVar(value=_read_startup())
        self._tray_var = tk.BooleanVar(value=self._settings.get("minimize_to_tray", False))

        self._build_ui()

    def _load_settings(self) -> dict:
        if self._settings_path.exists():
            with open(self._settings_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_settings(self):
        with open(self._settings_path, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=4)

    def _build_ui(self):
        self.columnconfigure(0, weight=1)

        frame = ttk.LabelFrame(self, text="Application Settings")
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        frame.columnconfigure(0, weight=1)

        startup_cb = ttk.Checkbutton(
            frame,
            text="Start with Windows",
            variable=self._startup_var,
            command=self._on_startup_toggle,
        )
        startup_cb.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))

        ttk.Label(
            frame,
            text="Adds this app to the Windows startup registry (HKCU).",
            foreground="gray",
        ).grid(row=1, column=0, sticky="w", padx=28, pady=(0, 8))

        tray_cb = ttk.Checkbutton(
            frame,
            text="Minimize to tray on close",
            variable=self._tray_var,
            command=self._on_tray_toggle,
        )
        tray_cb.grid(row=2, column=0, sticky="w", padx=12, pady=(4, 4))

        ttk.Label(
            frame,
            text="Clicking X hides the window to the system tray instead of quitting.",
            foreground="gray",
        ).grid(row=3, column=0, sticky="w", padx=28, pady=(0, 12))

    def _on_startup_toggle(self):
        enabled = self._startup_var.get()
        if not _set_startup(enabled, _get_startup_exe()):
            self._startup_var.set(not enabled)

    def _on_tray_toggle(self):
        self._settings["minimize_to_tray"] = self._tray_var.get()
        self._save_settings()

    def get_minimize_to_tray(self) -> bool:
        return self._tray_var.get()
