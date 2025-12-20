from utils.autostart import enable_autostart
from utils.first_launch import is_first_launch, mark_first_launch_done
import tkinter as tk
from tkinter import ttk, messagebox
from pytubefix import YouTube
from download_window import DownloadWindow
from library_window import LibraryWindow
from utils.library_manager import get_library_count
from utils.window_pos_helper import center_window
from tray import SystemTray

CLIPBOARD_TRIGGER = "start_download"


class Pica:
    def __init__(self, root):
        if is_first_launch():
            enable_autostart("Pica")
            mark_first_launch_done()

        self.root = root
        self.root.title("Pica – YouTube Video Downloader")
        icon = tk.PhotoImage(file="icon.png")
        root.iconphoto(True, icon)
        center_window(self.root, 420, 120)
        self.root.resizable(False, False)

        self.tray = SystemTray(self.root)
        self.tray.start()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)


        self.last_clip = ""

        self.build_ui()
        self.poll_clipboard()

    def hide_to_tray(self):
        self.root.withdraw()


    def build_ui(self):
        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill="both", expand=True)

        top_row = ttk.Frame(frame)
        top_row.pack(fill="x")

        ttk.Label(
            top_row,
            text="YouTube Video URL:"
        ).pack(side="left")

        count = get_library_count()
        library_link = ttk.Label(
            top_row,
            text=f"Library ({count})",
            cursor="hand2",
            foreground="#188038",  # subtle link blue
            font=("Segoe UI", 9, "bold")
        )
        library_link.pack(side="right")

        library_link.bind("<Button-1>", self.open_library)


        self.url_entry = ttk.Entry(frame)
        self.url_entry.pack(fill="x", pady=(5, 10))
        self.url_entry.focus()

        self.download_btn = ttk.Button(
            frame,
            text="Download",
            command=self.on_download_clicked
        )
        self.download_btn.pack()

    # -------------------------------
    # Manual download (button click)
    # -------------------------------
    def on_download_clicked(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a video URL")
            return

        if not self.is_youtube_url(url):
            messagebox.showerror("Error", "Invalid YouTube URL")
            return

        try:
            yt = YouTube(url)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.url_entry.delete(0, tk.END)

        DownloadWindow(self.root, yt)
        self.root.withdraw()

    # -------------------------------
    # Clipboard watcher
    # -------------------------------
    def poll_clipboard(self):
        try:
            text = self.root.clipboard_get().strip()
        except tk.TclError:
            text = ""

        # if text and text != self.last_clip: 
        # self.last_clip = text

        if CLIPBOARD_TRIGGER in text:
            url = text.replace(CLIPBOARD_TRIGGER, "").strip()
            if self.is_youtube_url(url):
                self.handle_clipboard_download(url)

        self.root.after(800, self.poll_clipboard)

    def handle_clipboard_download(self, url):
        try:
            yt = YouTube(url)
        except Exception:
            return

        # Clear clipboard so it triggers only once
        self.root.clipboard_clear()

        # Open download window
        DownloadWindow(self.root, yt)
        self.root.withdraw()

    # -------------------------------
    # URL validation
    # -------------------------------
    def is_youtube_url(self, url):
        return (
            url.startswith("https://www.youtube.com/")
            or url.startswith("https://youtu.be/")
        )


    # -------------------------------
    # Library
    # -------------------------------
    def open_library(self, event=None):
        LibraryWindow(self.root)


if __name__ == "__main__":
    root = tk.Tk()

    app = DownloaderApp(root)

    # Hide to tray AFTER Tk initializes
    root.after(0, root.withdraw)

    root.mainloop()
