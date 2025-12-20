import threading
import pystray
from pystray import MenuItem as item
from PIL import Image
from utils.resource_path import resource_path


class SystemTray:
    def __init__(self, root):
        self.root = root
        self.icon = None

    def start(self):
        image = Image.open("icon.png")

        menu = (
            item("Open Pica", self.show_app),
            item("Library", self.open_library),
            item("Exit", self.exit_app),
        )

        self.icon = pystray.Icon(
            "Pica",
            image,
            "Pica – YT Video Downloader \nKeep it running to download videos.",
            menu
        )

        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_app(self):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def open_library(self):
        def _open():
            from library_window import LibraryWindow
            LibraryWindow(self.root)

        self.root.after(0, _open)

    def exit_app(self):
        self.icon.stop()
        self.root.after(0, self.root.destroy)
