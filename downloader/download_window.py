import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os
import webbrowser
import subprocess
from utils.window_pos_helper import center_window
from tools.ffmpeg_helper import merge_audio_video

from utils.files import safe_filename, get_unique_path
from utils.formatters import format_time, format_size
from utils.save_settings import get_default_download_path, save_download_path
from utils.library_manager import add_to_library


class DownloadWindow:
    def __init__(self, parent, yt):
        self.yt = yt

        self.phase = {
            "stream": None,
            "label": None,
            "started": False
        }

        self.remaining_mode = "na"  # values: "na", "calculating", "active", "done" 


        self.phase_start_time = None
        self.total_elapsed_time = 0.0

        self.is_downloading = False
        self.last_speed = 0
        self.last_remaining = 0
        self.display_progress = 0
        self.target_progress = 0    
        self.start_time = None
        self.cancel_event = threading.Event()
        self.merge_done = False  

        self.win = tk.Toplevel(parent)
        self.win.title("Preparing...")
        center_window(self.win, 420, 390)
        self.win.resizable(False, False)
        self.win.deiconify()
        self.win.lift()

        try:
            self.build_ui()
        except:
            messagebox.showerror(
                "Unexpected Error",
                "Pica is unable to download this video.\nAn unexpected error occurred."
            )
            self.win.destroy()
            return
        self.win.title("Downloading with Pica")


    def build_ui(self):
        self.frame = ttk.Frame(self.win, padding=15)
        self.frame.pack(fill="both", expand=True)

        yt_title = self.yt.title
        if len(yt_title) > 60:
            yt_title = f"{yt_title[:60]} ..."

        ttk.Label(self.frame, text=yt_title, wraplength=380).pack(anchor="w", pady=(0, 10))

        self.select_frame = ttk.Frame(self.frame)
        self.select_frame.pack(fill="x")

        ttk.Label(self.select_frame, text="Quality:").pack(anchor="w")

        
        video_streams = (
            self.yt.streams
            .filter(file_extension="mp4")
            .order_by("resolution")
            .desc()
        )


        best_audio = (
            self.yt.streams
            .filter(only_audio=True, mime_type="audio/mp4")
            .order_by("abr")
            .desc()
            .first()
        )

        # safe fallback
        if not best_audio:
            best_audio = (
                self.yt.streams
                .filter(only_audio=True)
                .order_by("abr")
                .desc()
                .first()
            )


        streams_by_resolution = {}

        for stream in video_streams:
            res = stream.resolution
            if not res:
                continue

            if res not in streams_by_resolution:
                streams_by_resolution[res] = stream
            else:
                if stream.is_progressive and not streams_by_resolution[res].is_progressive:
                    streams_by_resolution[res] = stream

        if not streams_by_resolution and not best_audio:
            messagebox.showerror("Error", "No downloadable streams found")
            self.win.destroy()
            return

        self.stream_map = {}
        options = []

        for res in sorted(
            streams_by_resolution.keys(),
            key=lambda x: int(x.replace("p", "")),
            reverse=True
        ):
            stream = streams_by_resolution[res]
            size_mb = stream.filesize_approx / (1024 * 1024)
            label = f"{res}  •  {size_mb:.1f} MB"
            self.stream_map[label] = stream
            options.append(label)

        if best_audio:
            size_mb = best_audio.filesize_approx / (1024 * 1024)
            label = f"Audio  •  {size_mb:.1f} MB"
            self.stream_map[label] = best_audio
            options.append(label)

        self.quality_var = tk.StringVar(value=options[0])

        ttk.Combobox(
            self.select_frame,
            textvariable=self.quality_var,
            values=options,
            state="readonly"
        ).pack(fill="x", pady=(5, 10))

        self.save_path = tk.StringVar(value=get_default_download_path())

        ttk.Button(
            self.select_frame,
            text="Choose Save Location",
            command=self.choose_folder
        ).pack(anchor="w")

        ttk.Label(
            self.select_frame,
            textvariable=self.save_path
        ).pack(anchor="w", pady=(2, 10))

        self.progress = tk.IntVar(value=0)

        ttk.Progressbar(
            self.frame,
            variable=self.progress
        ).pack(fill="x", pady=(10, 2))

        self.percent_label = ttk.Label(self.frame, text="0%")
        self.percent_label.pack(anchor="e")

        self.size_label = ttk.Label(self.frame, text="File size: Na")
        self.size_label.pack(anchor="w")

        self.speed_label = ttk.Label(self.frame, text="Speed: Na")
        self.speed_label.pack(anchor="w")

        self.elapsed_label = ttk.Label(self.frame, text="Elapsed: Na")
        self.elapsed_label.pack(anchor="w")

        self.remaining_label = ttk.Label(self.frame, text="Remaining: Na")
        self.remaining_label.pack(anchor="w")

        self.status_label = ttk.Label(self.frame, text="Status: Waiting", foreground="#5F6368")
        self.status_label.pack(anchor="w", pady=(5, 5))

        self.action_frame = ttk.Frame(self.frame)
        self.action_frame.pack(pady=(10, 0))

        self.action_btn = ttk.Button(
            self.action_frame,
            text="Start Download",
            command=self.start_download
        )
        self.action_btn.pack()

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_path.get())
        if folder:
            self.save_path.set(folder)
            save_download_path(folder)

    def start_download(self):
        self.stream = self.stream_map.get(self.quality_var.get())
        self.is_progressive = self.stream.is_progressive
        self.is_audio_only = self.stream.type == "audio"

        self.select_frame.destroy()
        center_window(self.win, 420, 280)

        self.action_btn.config(text="Cancel", command=self.cancel_download)

        # show initial state
        self.status_label.config(text="Status: Connecting…", foreground="#6A1B9A")

        self.remaining_mode = "calculating"
        self.last_remaining = 0


        # initial phase intent (NO progress yet)
        self.phase["stream"] = self.stream
        self.phase["label"] = None   # <-- important
        self.phase["started"] = False

        self.start_time = time.time()
        self.total_size = self.stream.filesize or self.stream.filesize_approx

        self.size_label.config(
            text=f"File size: {format_size(self.total_size)}"
        )

        self.yt.register_on_progress_callback(self.on_progress)

        self.is_downloading = True
        self.start_ui_progress_loop()

        self.phase_start_time = time.time()
        threading.Thread(target=self.download_task, daemon=True).start()


    # -------------------------------
    # UI ticker for smooth progress
    # -------------------------------
    def start_ui_progress_loop(self):
        def tick():
            # smooth progress bar
            if self.display_progress < self.target_progress:
                self.display_progress += 1
                self.progress.set(self.display_progress)
                self.percent_label.config(text=f"{self.display_progress}%")

            # ⏱ smooth elapsed time (REAL TIME)
            if self.start_time:
                elapsed = time.time() - self.start_time
                self.elapsed_label.config(
                    text=f"Elapsed: {format_time(elapsed)}"
                )

            # 🚀 smooth speed + remaining (cached)
            self.speed_label.config(
                text=f"Speed: {format_size(self.last_speed)}/s"
            )

            if self.remaining_mode == "calculating":
                self.remaining_label.config(text="Remaining: Calculating")
            elif self.remaining_mode == "na":
                self.remaining_label.config(text="Remaining: Na")
            elif self.remaining_mode == "done":
                self.remaining_label.config(text="Remaining: 00:00:00")
            else:  # active
                self.remaining_label.config(
                    text=f"Remaining: {format_time(self.last_remaining)}"
                )


            if self.is_downloading:
                self.win.after(100, tick)

        tick()


    def download_task(self):

        try:
            if self.is_audio_only:
                folder = self.save_path.get()
                filename = safe_filename(self.yt.title) + ".m4a"
                self.final_file_path = get_unique_path(folder, filename)

                self.start_phase(self.stream, "Downloading")
                self.stream.download(
                    output_path=folder,
                    filename=os.path.basename(self.final_file_path)
                )
            elif self.is_progressive:
                folder = self.save_path.get()
                filename = safe_filename(self.yt.title) + ".mp4"
                self.final_file_path = get_unique_path(folder, filename)

                self.start_phase(self.stream, "Downloading")
                self.stream.download(
                    output_path=folder,
                    filename=os.path.basename(self.final_file_path)
                )

            else:
                self.download_adaptive()

            self.remaining_mode = "done"
            self.last_remaining = 0

            # ✅ FORCE final repaint (important)
            self.remaining_label.config(text="Remaining: 00:00:00")
            self.win.after(0, self.on_complete)
        except Exception:
            pass
        finally:
            if self.cancel_event.is_set():
                try:
                    if hasattr(self, "final_file_path") and os.path.exists(self.final_file_path):
                        os.remove(self.final_file_path)
                except Exception:
                    pass
            
    # merge progress animation
    # -------------------------------
    def start_merge_progress(self):
        self.merge_progress = 0
        self.merge_done = False
        self.progress.set(0)
        self.percent_label.config(text="0%")

        def tick():
            if self.merge_done:
                return
            if self.merge_progress < 95:
                self.merge_progress += 1
                self.progress.set(self.merge_progress)
                self.percent_label.config(text=f"{self.merge_progress}%")
                self.win.after(80, tick)

        tick()

    def download_adaptive(self):
        base = self.save_path.get()

        # reset for video download
        self.start_phase(self.stream, "Downloading Video")
        video_path = self.stream.download(base, filename="video_only.mp4")

        # prepare audio
        audio = (
            self.yt.streams
            .filter(only_audio=True, mime_type="audio/mp4")
            .order_by("abr")
            .desc()
            .first()
        ) or (
            self.yt.streams
            .filter(only_audio=True)
            .order_by("abr")
            .desc()
            .first()
        )

        # ✅ show connecting again (new request)
        self.win.after(
            0,
            lambda: self.status_label.config(
                text="Status: Connecting…",
                foreground="#6A1B9A"
            )
        )

        # start audio phase
        self.start_phase(audio, "Downloading Audio")
        audio_path = audio.download(base, filename="audio_only.m4a")


        self.win.after(
            0,
            lambda *_: (
                setattr(self, "is_downloading", False),  # STOP main loop
                self.action_btn.config(state="disabled"),
                self.status_label.config(text="Status: Merging", foreground="#F4B400"),
                self.start_merge_progress(),
            )
        )

        safe_title = safe_filename(self.yt.title)

        filename = f"{safe_title}.mp4"
        output = get_unique_path(base, filename)
        self.final_file_path = output


        self.remaining_mode = "na"
        self.last_remaining = 0
        merge_audio_video(video_path, audio_path, output)

        self.merge_done = True
        self.is_downloading = False
        self.target_progress = 100
        self.display_progress = 100

        if self.cancel_event.is_set():
            return 

        self.win.after(
            0,
            lambda *_: (
                self.progress.set(100),
                self.percent_label.config(text="100%")
            )
        )

        try:
            os.remove(video_path)
            os.remove(audio_path)
        except Exception:
            pass

    def start_phase(self, stream, label):

        # ⏱ close previous phase timing
        if self.phase_start_time is not None:
            self.total_elapsed_time += time.time() - self.phase_start_time

        # start new phase timing
        self.phase_start_time = time.time()

        self.phase["stream"] = stream
        self.phase["label"] = label
        self.phase["started"] = False

        # ✅ RESET remaining logic HERE
        self.remaining_mode = "calculating"
        self.last_remaining = 0

        self.total_size = stream.filesize or stream.filesize_approx
        self.start_time = time.time()

        self.display_progress = 0
        self.target_progress = 0
        self.last_speed = 0
        self.last_remaining = 0

        self.progress.set(0)
        self.percent_label.config(text="0%")
        self.size_label.config(
            text=f"File size: {format_size(self.total_size)}"
        )

        self.yt.register_on_progress_callback(self.on_progress)



    def cancel_download(self):
        self.cancel_event.set()
        self.status_label.config(text="Status: Cancelled", foreground="#D93025")
        self.win.after(600, self.win.destroy)

    def highlight_window(self):
        try:
            # Bring attention without stealing focus
            self.win.deiconify()
            self.win.lift()
            self.win.attributes("-topmost", True)
            self.win.after(200, lambda: self.win.attributes("-topmost", False))
        except Exception:
            pass

    def open_support_link(self, event=None):
        try:
            import webbrowser
            webbrowser.open("https://www.buymeacoffee.com/mshezikhan")
        except Exception:
            pass  # fail silently


    def on_complete(self):
        if self.cancel_event.is_set():
            return  

        # ⏱ close last phase
        if self.phase_start_time is not None:
            self.total_elapsed_time += time.time() - self.phase_start_time
            self.phase_start_time = None

        self.is_downloading = False
        self.target_progress = 100
        self.display_progress = 100
        self.progress.set(100)
        self.percent_label.config(text="100%")
        self.elapsed_label.config(
            text=f"Elapsed: {format_time(self.total_elapsed_time)}"
        )

        self.status_label.config(text="Status: Completed", foreground="#188038")

        # clear old button
        for w in self.action_frame.winfo_children():
            w.destroy()

        # buttons row
        btn_row = ttk.Frame(self.action_frame)
        btn_row.pack()

        ttk.Button(
            btn_row,
            text="Open",
            command=self.open_file
        ).pack(side="left", padx=(0, 16))

        ttk.Button(
            btn_row,
            text="Open Folder",
            command=self.open_folder
        ).pack(side="left", padx=(0, 16))

        ttk.Button(
            btn_row,
            text="Library",
            command=self.open_library
        ).pack(side="left")


        support = tk.Label(
            self.action_frame,
            text="Support Pica",
            fg="#1A73E8",
            cursor="hand2",
            font=("Segoe UI", 9, "underline")
        )
        support.pack(pady=(10, 0))

        support.bind("<Button-1>", self.open_support_link)


        # Add to Library
        try:
            add_to_library(self.yt, self.final_file_path)
        except Exception:
            pass

        self.highlight_window()


    def open_file(self):
        path = self.final_file_path

        try:
            if os.name == "nt":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

        # ✅ close download window
        self.win.after(200, self.win.destroy)


    def open_folder(self):
        path = self.save_path.get()

        if os.name == "nt":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])

        # ✅ close download window after opening folder
        self.win.after(200, self.win.destroy)


    def open_library(self):
        try:
            from library_window import LibraryWindow

            # ✅ DO NOT restore main window
            LibraryWindow(self.win.master)

        except Exception:
            pass

        # close download window
        self.win.after(200, self.win.destroy)


    # -------------------------------
    # download callback (NO UI here)
    # -------------------------------
    def on_progress(self, stream, chunk, bytes_remaining):
        if stream != self.phase["stream"]:
            return
        if self.cancel_event.is_set():
            return

        if not self.phase["started"]:
            self.phase["started"] = True
            self.remaining_mode = "active"
            self.win.after(
                0,
                lambda: self.status_label.config(
                    text=f"Status: {self.phase['label']}",
                    foreground="#1A73E8"
                )
            )


        downloaded = self.total_size - bytes_remaining
        self.target_progress = int(downloaded / self.total_size * 100)

        elapsed = time.time() - self.start_time
        speed = downloaded / elapsed if elapsed > 0 else 0
        remaining = (self.total_size - downloaded) / speed if speed > 0 else 0

        self.last_speed = speed
        self.last_remaining = remaining
