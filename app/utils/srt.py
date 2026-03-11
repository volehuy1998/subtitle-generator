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
