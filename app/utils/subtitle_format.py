"""Subtitle formatting utilities: line-breaking, CPS validation, word-level rendering."""



# Default constraints
DEFAULT_MAX_CHARS_PER_LINE = 42
DEFAULT_MAX_LINES = 2
DEFAULT_MAX_CPS = 25  # Characters per second (Netflix standard: 20, YouTube: ~25)
DEFAULT_MIN_DURATION = 0.7  # Minimum subtitle display duration in seconds
DEFAULT_MAX_DURATION = 7.0  # Maximum subtitle display duration in seconds


def break_line(text: str, max_chars: int = DEFAULT_MAX_CHARS_PER_LINE,
               max_lines: int = DEFAULT_MAX_LINES) -> str:
    """Break a subtitle line according to rules.

    Rules:
    - Split at sentence boundaries first (. ! ? ;)
    - Then at clause boundaries (, : -)
    - Then at word boundaries, preferring near the middle
    - Never split mid-word
    """
    text = text.strip()
    if len(text) <= max_chars:
        return text

    if max_lines < 2:
        return text[:max_chars].rsplit(" ", 1)[0] if " " in text[:max_chars] else text[:max_chars]

    # Try sentence boundaries
    for sep in [". ", "! ", "? ", "; "]:
        idx = text.find(sep)
        if 0 < idx < len(text) - 2:
            line1 = text[:idx + 1].strip()
            line2 = text[idx + 1:].strip()
            if len(line1) <= max_chars and len(line2) <= max_chars:
                return f"{line1}\n{line2}"

    # Try clause boundaries
    for sep in [", ", ": ", " - "]:
        idx = text.find(sep)
        if 0 < idx < len(text) - 2:
            line1 = text[:idx + len(sep) - 1].strip()
            line2 = text[idx + len(sep) - 1:].strip()
            if len(line1) <= max_chars and len(line2) <= max_chars:
                return f"{line1}\n{line2}"

    # Split at middle word boundary
    words = text.split()
    if len(words) < 2:
        return text

    mid = len(text) // 2
    best_split = 0
    best_diff = len(text)
    pos = 0
    for i, word in enumerate(words[:-1]):
        pos += len(word) + 1
        diff = abs(pos - mid)
        if diff < best_diff:
            best_diff = diff
            best_split = i + 1

    line1 = " ".join(words[:best_split])
    line2 = " ".join(words[best_split:])
    if len(line1) <= max_chars and len(line2) <= max_chars:
        return f"{line1}\n{line2}"

    # Fallback: hard split at max_chars
    return text[:max_chars].rsplit(" ", 1)[0] + "\n" + text[max_chars:].strip() if " " in text[:max_chars] else text


def calculate_cps(text: str, duration: float) -> float:
    """Calculate characters per second for a subtitle."""
    if duration <= 0:
        return 0.0
    clean = text.replace("\n", " ").strip()
    return len(clean) / duration


def validate_timing(start: float, end: float, text: str,
                    max_cps: float = DEFAULT_MAX_CPS,
                    min_duration: float = DEFAULT_MIN_DURATION,
                    max_duration: float = DEFAULT_MAX_DURATION) -> dict:
    """Validate subtitle timing and return diagnostics."""
    duration = end - start
    cps = calculate_cps(text, duration)
    issues = []

    if duration < min_duration:
        issues.append(f"too_short ({duration:.2f}s < {min_duration}s)")
    if duration > max_duration:
        issues.append(f"too_long ({duration:.2f}s > {max_duration}s)")
    if cps > max_cps:
        issues.append(f"too_fast ({cps:.1f} CPS > {max_cps})")
    if len(text.strip()) == 0:
        issues.append("empty_text")

    return {
        "duration": round(duration, 3),
        "cps": round(cps, 1),
        "char_count": len(text.replace("\n", " ").strip()),
        "valid": len(issues) == 0,
        "issues": issues,
    }


def format_segments_with_linebreaks(segments: list,
                                     max_chars: int = DEFAULT_MAX_CHARS_PER_LINE,
                                     max_lines: int = DEFAULT_MAX_LINES) -> list:
    """Apply line-breaking rules to all segments."""
    result = []
    for seg in segments:
        formatted = dict(seg)
        formatted["text"] = break_line(seg["text"], max_chars, max_lines)
        result.append(formatted)
    return result


def words_to_segments(words: list, max_chars: int = DEFAULT_MAX_CHARS_PER_LINE,
                      max_gap: float = 1.5, max_segment_duration: float = 7.0) -> list:
    """Group word-level timestamps into subtitle segments.

    Args:
        words: List of {"word": str, "start": float, "end": float, "probability": float}
        max_chars: Maximum characters per subtitle line
        max_gap: Maximum silence gap before forcing a new segment
        max_segment_duration: Maximum duration of a single segment
    """
    if not words:
        return []

    segments = []
    current_words = []
    current_text = ""
    seg_start = words[0]["start"]

    for i, w in enumerate(words):
        word_text = w["word"].strip()
        if not word_text:
            continue

        new_text = (current_text + " " + word_text).strip() if current_text else word_text
        duration = w["end"] - seg_start

        # Check if we should start a new segment
        force_split = False
        if current_words:
            gap = w["start"] - current_words[-1]["end"]
            if gap > max_gap:
                force_split = True
            elif duration > max_segment_duration:
                force_split = True
            elif len(new_text) > max_chars * 2:  # Allow 2 lines
                force_split = True

        if force_split and current_words:
            segments.append({
                "start": seg_start,
                "end": current_words[-1]["end"],
                "text": break_line(current_text, max_chars),
                "words": list(current_words),
            })
            current_words = []
            current_text = ""
            seg_start = w["start"]

        current_words.append(w)
        current_text = (current_text + " " + word_text).strip() if current_text else word_text

    # Flush remaining
    if current_words:
        segments.append({
            "start": seg_start,
            "end": current_words[-1]["end"],
            "text": break_line(current_text, max_chars),
            "words": list(current_words),
        })

    return segments
