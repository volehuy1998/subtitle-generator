"""SRT and VTT subtitle file generation with speaker labels and word-level support."""

import json
from app.utils.formatting import format_timestamp


def segments_to_srt(segments: list, include_speakers: bool = True) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = seg["text"].strip()
        # Prepend speaker label if available
        speaker = seg.get("speaker")
        if include_speakers and speaker:
            text = f"[{speaker}] {text}"
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def _format_vtt_timestamp(seconds: float) -> str:
    """VTT uses '.' instead of ',' for milliseconds."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def segments_to_vtt(segments: list, include_speakers: bool = True) -> str:
    lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments, 1):
        start = _format_vtt_timestamp(seg["start"])
        end = _format_vtt_timestamp(seg["end"])
        text = seg["text"].strip()
        speaker = seg.get("speaker")
        if include_speakers and speaker:
            text = f"<v {speaker}>{text}"
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def _parse_srt_timestamp(ts: str) -> float:
    """Parse SRT timestamp (HH:MM:SS,mmm) to float seconds."""
    ts = ts.strip()
    main, ms = ts.split(",")
    parts = main.split(":")
    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
    return h * 3600 + m * 60 + s + int(ms) / 1000.0


def _parse_vtt_timestamp(ts: str) -> float:
    """Parse VTT timestamp (HH:MM:SS.mmm) to float seconds."""
    ts = ts.strip()
    main, ms = ts.split(".")
    parts = main.split(":")
    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
    return h * 3600 + m * 60 + s + int(ms) / 1000.0


def parse_srt(srt_content: str) -> list[dict]:
    """Parse SRT string into list of segment dicts: [{start, end, text}, ...].

    Handles standard SRT format: index, timestamp --> timestamp, text, blank line.
    """
    segments = []
    blocks = srt_content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        # Find the timestamp line (contains " --> ")
        ts_idx = None
        for i, line in enumerate(lines):
            if " --> " in line:
                ts_idx = i
                break
        if ts_idx is None:
            continue
        ts_parts = lines[ts_idx].split(" --> ")
        if len(ts_parts) != 2:
            continue
        start = _parse_srt_timestamp(ts_parts[0])
        end = _parse_srt_timestamp(ts_parts[1])
        text = "\n".join(lines[ts_idx + 1:]).strip()
        if text:
            segments.append({"start": start, "end": end, "text": text})
    return segments


def parse_vtt(vtt_content: str) -> list[dict]:
    """Parse VTT string into list of segment dicts: [{start, end, text}, ...].

    Strips WEBVTT header and handles standard VTT cue format.
    """
    segments = []
    # Remove WEBVTT header
    content = vtt_content.strip()
    if content.startswith("WEBVTT"):
        # Skip header lines until first blank line
        idx = content.find("\n\n")
        if idx != -1:
            content = content[idx + 2:]
        else:
            return segments

    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        ts_idx = None
        for i, line in enumerate(lines):
            if " --> " in line:
                ts_idx = i
                break
        if ts_idx is None:
            continue
        ts_parts = lines[ts_idx].split(" --> ")
        if len(ts_parts) != 2:
            continue
        start = _parse_vtt_timestamp(ts_parts[0])
        end = _parse_vtt_timestamp(ts_parts[1])
        text = "\n".join(lines[ts_idx + 1:]).strip()
        if text:
            segments.append({"start": start, "end": end, "text": text})
    return segments


def segments_to_json(segments: list) -> str:
    """Export segments as JSON with full word-level data (for karaoke-style rendering)."""
    output = []
    for seg in segments:
        entry = {
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
        }
        if "speaker" in seg:
            entry["speaker"] = seg["speaker"]
        if "words" in seg:
            entry["words"] = seg["words"]
        output.append(entry)
    return json.dumps(output, indent=2, ensure_ascii=False)
