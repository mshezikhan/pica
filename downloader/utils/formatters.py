def format_time(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def format_size(bytes_value):
    if bytes_value < 1024:
        return f"{bytes_value:.0f} B"
    elif bytes_value < 1024 ** 2:
        return f"{bytes_value / 1024:.2f} KB"
    else:
        return f"{bytes_value / (1024 ** 2):.2f} MB"
