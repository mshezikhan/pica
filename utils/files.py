import os

def safe_filename(name):
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        name = name.replace(ch, '')
    return name.strip()

def get_unique_path(folder, filename):
    name, ext = os.path.splitext(filename)
    counter = 1
    final_path = os.path.join(folder, filename)

    while os.path.exists(final_path):
        final_path = os.path.join(folder, f"{name} ({counter}){ext}")
        counter += 1

    return final_path
