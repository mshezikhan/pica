import os
from utils.app_paths import app_data_path

SAVE_SETTINGS_FILE = app_data_path("last_save_folder.txt")

APP_DIR_NAME = ".pica"


SAVE_SETTINGS_FILE = app_data_path("last_save_folder.txt")


def get_default_download_path():
    """
    Returns last saved folder if valid, else Downloads/Pica.
    """
    try:
        if os.path.exists(SAVE_SETTINGS_FILE):
            with open(SAVE_SETTINGS_FILE, "r", encoding="utf-8") as f:
                path = f.read().strip()
                if path and os.path.isdir(path):
                    return path
    except Exception:
        pass

    # default path
    path = os.path.join(os.path.expanduser("~"), "Downloads", "Pica")
    os.makedirs(path, exist_ok=True)
    return path



def save_download_path(path: str):
    """
    Saves selected download folder.
    """
    try:
        with open(SAVE_SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.write(path)
    except Exception:
        pass
