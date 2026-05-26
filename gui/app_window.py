import tkinter as tk
from tkinter import ttk
import pathlib

from .tab_setup import SetupTab
from .tab_recording import RecordingTab
from .tab_analysis import AnalysisTab
from .tab_settings import SettingsTab
from .tray import TrayIcon


class AppWindow(ttk.Frame):
    def __init__(self, parent, base_dir):
        super().__init__(parent)
        self._base_dir = pathlib.Path(base_dir)
        self._tray = None

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.tab_setup = SetupTab(notebook, base_dir)
        self.tab_recording = RecordingTab(notebook, base_dir)
        self.tab_analysis = AnalysisTab(notebook, base_dir)
        self.tab_settings = SettingsTab(notebook, base_dir)

        notebook.add(self.tab_setup, text="  Setup  ")
        notebook.add(self.tab_recording, text="  Recording  ")
        notebook.add(self.tab_analysis, text="  Analysis  ")
        notebook.add(self.tab_settings, text="  Settings  ")

        notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        self._notebook = notebook

    def _on_tab_change(self, event):
        selected = event.widget.tab("current", "text").strip()
        if selected == "Analysis":
            self.tab_analysis.load_and_render()

    def _show_window(self):
        self.master.after(0, self._do_show)

    def _do_show(self):
        self.master.deiconify()
        self.master.lift()
        self.master.focus_force()

    def _quit_app(self):
        self.master.after(0, self._do_quit)

    def _do_quit(self):
        self.tab_recording.stop_if_running()
        if self._tray:
            self._tray.stop()
        self.master.destroy()

    def on_close(self):
        if self.tab_settings.get_minimize_to_tray():
            if self._tray is None:
                self._tray = TrayIcon(self._base_dir, self._show_window, self._quit_app)
                self._tray.start()
            self.master.withdraw()
        else:
            self._do_quit()
