import os
from utils.app_paths import app_data_path

FLAG_FILE = app_data_path("first_launch_done.txt")


def is_first_launch():
    return not os.path.exists(FLAG_FILE)


def mark_first_launch_done():
    with open(FLAG_FILE, "w", encoding="utf-8") as f:
        f.write("done")
