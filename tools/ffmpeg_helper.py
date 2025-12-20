import subprocess
import os
import sys
from utils.resource_path import resource_path


def merge_audio_video(video_path, audio_path, output_path):
    ffmpeg =  resource_path("tools/ffmpeg/ffmpeg.exe")

    cmd = [
        ffmpeg,
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c", "copy",
        output_path
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check = True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
