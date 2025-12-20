from datetime import datetime, date


def humanize_date(date_str):
    """
    Convert YYYY-MM-DD to:
    - Today
    - Yesterday
    - X days ago
    - X months ago
    - X years ago
    """

    try:
        published = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return date_str  # fallback, never crash UI

    today = date.today()
    delta_days = (today - published).days

    if delta_days < 0:
        return date_str  # future date safety

    if delta_days == 0:
        return "Today"
    if delta_days == 1:
        return "Yesterday"
    if delta_days < 30:
        return f"{delta_days} days ago"
    if delta_days < 365:
        months = delta_days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"

    years = delta_days // 365
    return f"{years} year{'s' if years > 1 else ''} ago"
