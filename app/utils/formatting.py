"""Pure formatting functions. No external dependencies."""


def format_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    elif b < 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024):.1f} MB"
    else:
        return f"{b / (1024 * 1024 * 1024):.2f} GB"


def format_timestamp(seconds: float) -> str:
    """SRT timestamp format: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_time_display(seconds: float) -> str:
    """Human-readable duration: 5s, 2m 30s, 1h 5m."""
    if seconds < 0:
        return "calculating..."
    if seconds < 1:
        return "<1s"
    if seconds < 60:
        return f"{int(seconds)}s"
    m = int(seconds // 60)
    s = int(seconds % 60)
    if m < 60:
        return f"{m}m {s}s"
    h = int(m // 60)
    m = m % 60
    return f"{h}h {m}m"


def format_time_short(seconds: float) -> str:
    """Short time format for segment display: M:SS.S"""
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:04.1f}"
