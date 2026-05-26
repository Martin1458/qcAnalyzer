import threading
import pathlib
import pystray
from PIL import Image


def _load_icon(base_dir: pathlib.Path) -> Image.Image:
    icon_path = base_dir / "icon.png"
    img = Image.open(icon_path).convert("RGBA")
    img = img.resize((64, 64), Image.LANCZOS)
    return img


class TrayIcon:
    def __init__(self, base_dir: pathlib.Path, on_show, on_quit):
        self._on_show = on_show
        self._on_quit = on_quit
        self._icon = None
        self._base_dir = base_dir

    def start(self):
        image = _load_icon(self._base_dir)
        menu = pystray.Menu(
            pystray.MenuItem("Show", self._handle_show, default=True),
            pystray.MenuItem("Quit", self._handle_quit),
        )
        self._icon = pystray.Icon("RLQCAnalyzer", image, "RL QC Analyzer", menu)
        threading.Thread(target=self._icon.run, daemon=True).start()

    def stop(self):
        if self._icon:
            self._icon.stop()
            self._icon = None

    def _handle_show(self, icon, item):
        self._on_show()

    def _handle_quit(self, icon, item):
        self._on_quit()
