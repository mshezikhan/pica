import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import subprocess
import hashlib
from datetime import datetime
from PIL import Image, ImageTk
from utils.app_paths import app_cache_dir
from utils.humanize_date import humanize_date
from utils.library_manager import (
    load_library,
    remove_from_library,
    get_library_count
)

# ------------------------------
# Config
# ------------------------------

THUMB_SIZE = (440, 248)
COLUMNS = 4

THUMB_CACHE_DIR = app_cache_dir("thumbs")


# ------------------------------
# Helpers
# ------------------------------

def open_file(path):
    if not os.path.exists(path):
        return False

    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform.startswith("darwin"):
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

    return True


def open_file_location(path):
    if not os.path.exists(path):
        return

    if sys.platform.startswith("win"):
        subprocess.Popen(
            ["explorer", "/select,", os.path.normpath(path)]
        )
    elif sys.platform.startswith("darwin"):
        subprocess.Popen(["open", "-R", path])
    else:
        subprocess.Popen(["xdg-open", os.path.dirname(path)])



# ------------------------------
# Library Window
# ------------------------------

class LibraryWindow:
    def __init__(self, parent):
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title("Downloaded with Pica")
        self.win.state("zoomed")
        self.win.minsize(700, 400)
        self.win.lift()

        self.entries = []
        self.thumbnails = []  # keep references

        self.build_ui()
        self.load_library()

    # ------------------------------

    def build_ui(self):
        header = ttk.Frame(self.win, padding=(15, 12, 15, 6))
        header.pack(fill="x")

        # left side (title)
        self.title_label = ttk.Label(
            header,
            text=f"Library ({get_library_count()})",
            font=("Segoe UI", 14, "bold")
        )
        self.title_label.pack(side="left")

        # right side (refresh)
        refresh_btn = ttk.Button(
            header,
            text="⟳ Refresh",
            width=10,
            command=self.refresh
        )
        refresh_btn.pack(side="right")


        ttk.Separator(self.win).pack(fill="x")

        outer = ttk.Frame(self.win)
        outer.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(outer, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            outer, orient="vertical", command=self.canvas.yview
        )
        scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.grid_frame = ttk.Frame(self.canvas, padding=15)
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.grid_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

    # ------------------------------

    def load_library(self):
        self.entries = load_library()

        # ✅ Sort by download time (newest first)
        self.entries.sort(
            key=lambda x: x.get("downloaded_at", ""),
            reverse=True
        )

        grouped = {}
        for item in self.entries:
            author = item.get("author", "Unknown")
            grouped.setdefault(author, []).append(item)

        for author, items in grouped.items():
            self.render_author_group(author, items)

    # ------------------------------

    def render_author_group(self, author, items):
        ttk.Label(
            self.grid_frame,
            text=author,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(20, 8))

        group_frame = ttk.Frame(self.grid_frame)
        group_frame.pack(fill="x")

        row = col = 0
        for item in items:
            self.render_item(item, group_frame, row, col)
            col += 1
            if col >= COLUMNS:
                col = 0
                row += 1

        ttk.Separator(self.grid_frame).pack(fill="x", pady=(15, 5))

    # ------------------------------
    # Thumbnail helpers
    # ------------------------------

    @staticmethod
    def get_thumb_path(original_path):
        name = hashlib.md5(original_path.encode()).hexdigest()
        return os.path.join(THUMB_CACHE_DIR, f"{name}.jpg")

    def load_thumbnail(self, path):
        try:
            thumb_path = self.get_thumb_path(path)

            if os.path.exists(thumb_path):
                with Image.open(thumb_path) as im:
                    img = im.copy()
            else:
                with Image.open(path) as im:
                    im.thumbnail(THUMB_SIZE, Image.BILINEAR)
                    im.save(thumb_path, "JPEG", quality=85, optimize=True)
                    img = im.copy()

            return ImageTk.PhotoImage(img)

        except Exception:
            img = Image.new("RGB", THUMB_SIZE, "#222")
            return ImageTk.PhotoImage(img)

    # ------------------------------

    def render_item(self, item, parent, row, col):
        card = tk.Frame(parent, bd=1, relief="solid", bg="white")
        card.grid(row=row, column=col, padx=12, pady=12, sticky="n")

        placeholder = ImageTk.PhotoImage(
            Image.new("RGB", THUMB_SIZE, "#222")
        )
        self.thumbnails.append(placeholder)

        thumb = ttk.Label(card, image=placeholder)
        thumb.image = placeholder
        thumb.pack()

        self.win.after(
            10,
            lambda p=item.get("thumbnail", ""), l=thumb: self.set_thumb(p, l)
        )

        thumb.bind("<Button-1>", lambda e, i=item: self.on_open(i))
        thumb.bind("<Button-3>", lambda e, i=item: self.show_context_menu(e, i))

        self.bind_hover(card)

        ttk.Label(
            card,
            text=f"Uploaded • {humanize_date(item.get('publish_date', ''))}",
            font=("Segoe UI", 10, "bold"),
            foreground="#555",
            background="white"
        ).pack(pady=(8, 6))

    # ------------------------------

    def set_thumb(self, path, label):
        img = self.load_thumbnail(path)
        label.image = img
        label.config(image=img)
        self.thumbnails.append(img)

    # ------------------------------

    def show_context_menu(self, event, item):
        menu = tk.Menu(self.win, tearoff=0)
        menu.add_command(
            label="Open file location",
            command=lambda: open_file_location(item.get("path", ""))
        )
        menu.tk_popup(event.x_root, event.y_root)

    # ------------------------------

    def bind_hover(self, widget):
        widget.bind("<Enter>", lambda e: widget.configure(bg="#f7f7f7"))
        widget.bind("<Leave>", lambda e: widget.configure(bg="white"))

    # ------------------------------

    def on_open(self, item):
        path = item.get("path", "")
        if open_file(path):
            return

        self.win.attributes("-topmost", True)
        messagebox.showinfo(
            "Video not found",
            "Video is no longer available in downloaded location.\n"
            "It will be removed from Library.",
            parent=self.win
        )
        self.win.attributes("-topmost", False)

        self.remove_entry(item)
        self.refresh()

    # ------------------------------

    def remove_entry(self, item):
        self.entries = remove_from_library(item.get("id"))

    # ------------------------------

    def refresh(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        self.thumbnails.clear()
        self.load_library()

        # update header count
        self.title_label.config(
            text=f"Library ({get_library_count()})"
        )
