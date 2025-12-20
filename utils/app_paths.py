import os

APP_DIR_NAME = ".pica"

def app_data_dir():
    """
    Returns app data directory, creates it if missing.
    """
    base = os.path.join(os.path.expanduser("~"), APP_DIR_NAME)
    os.makedirs(base, exist_ok=True)
    return base


def app_data_path(filename: str) -> str:
    """
    Returns full path inside app data directory.
    """
    return os.path.join(app_data_dir(), filename)

def app_cache_dir(subdir: str = "") -> str:
    """
    Returns cache directory inside app data.
    """
    base = os.path.join(app_data_dir(), "cache")
    if subdir:
        base = os.path.join(base, subdir)
    os.makedirs(base, exist_ok=True)
    return base
