import json
import os
import requests
from datetime import datetime
from utils.app_paths import app_data_path, app_data_dir


# ----------------------------
# Paths
# ----------------------------

LIBRARY_JSON = app_data_path("library.json")
THUMBS_DIR = os.path.join(app_data_dir(), "thumbs")


def ensure_dirs():
    os.makedirs(app_data_dir(), exist_ok=True)
    os.makedirs(THUMBS_DIR, exist_ok=True)


# ----------------------------
# Library read / write
# ----------------------------

def load_library():
    if not os.path.exists(LIBRARY_JSON):
        return []

    try:
        with open(LIBRARY_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_library(entries):
    with open(LIBRARY_JSON, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def get_library_count():
    try:
        return len(load_library())
    except Exception:
        return 0


# ----------------------------
# Remove entry
# ----------------------------

def remove_from_library(video_id):
    entries = load_library()

    updated = []
    removed_item = None

    for e in entries:
        if e.get("id") == video_id:
            removed_item = e
        else:
            updated.append(e)

    if removed_item:
        thumb = removed_item.get("thumbnail")
        if thumb and os.path.exists(thumb):
            try:
                os.remove(thumb)
            except Exception:
                pass

        save_library(updated)

    return updated


# ----------------------------
# Thumbnail handling
# ----------------------------

def download_thumbnail(url, video_id):
    ensure_dirs()

    thumb_path = os.path.join(THUMBS_DIR, f"{video_id}.jpg")

    if os.path.exists(thumb_path):
        return thumb_path

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        with open(thumb_path, "wb") as f:
            f.write(r.content)
    except Exception:
        return ""

    return thumb_path


# ----------------------------
# Add entry
# ----------------------------

def add_to_library(yt, video_path):
    ensure_dirs()

    entries = load_library()

    # avoid duplicates
    for e in entries:
        if e.get("id") == yt.video_id:
            return

    thumb_path = download_thumbnail(
        yt.thumbnail_url,
        yt.video_id
    )

    publish_date = ""
    if yt.publish_date:
        publish_date = yt.publish_date.strftime("%Y-%m-%d")

    entry = {
        "id": yt.video_id,
        "title": yt.title or "Unknown",
        "author": yt.author or "Unknown",
        "publish_date": publish_date,
        "downloaded_at": datetime.now().isoformat(),
        "thumbnail": thumb_path,
        "path": video_path
    }

    entries.append(entry)
    save_library(entries)
