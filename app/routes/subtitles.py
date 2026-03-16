"""Subtitle editing routes - get and update segments."""

import json
import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app import state
from app.config import OUTPUT_DIR
from app.utils.srt import segments_to_srt, segments_to_vtt
from app.utils.validation import safe_path

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Subtitles"])


class Segment(BaseModel):
    start: float
    end: float
    text: str


class UpdateSubtitlesRequest(BaseModel):
    segments: list[Segment]


@router.get("/subtitles/{task_id}")
async def get_subtitles(task_id: str):
    """Get subtitle segments for editing."""
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    task = state.tasks[task_id]
    if task["status"] != "done":
        raise HTTPException(400, "Subtitles not ready yet")

    # Read segments from SRT file
    srt_path = safe_path(OUTPUT_DIR / f"{task_id}.srt", allowed_dir=OUTPUT_DIR)
    if not srt_path.exists():
        raise HTTPException(404, "Subtitle file not found")

    segments = _parse_srt(srt_path.read_text(encoding="utf-8"))
    return {"task_id": task_id, "segments": segments}


@router.put("/subtitles/{task_id}")
async def update_subtitles(task_id: str, req: UpdateSubtitlesRequest):
    """Update subtitle segments and regenerate SRT/VTT files."""
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    task = state.tasks[task_id]
    if task["status"] != "done":
        raise HTTPException(400, "Subtitles not ready yet")

    segments = [s.model_dump() for s in req.segments]

    # Regenerate files
    srt_path = safe_path(OUTPUT_DIR / f"{task_id}.srt", allowed_dir=OUTPUT_DIR)
    vtt_path = safe_path(OUTPUT_DIR / f"{task_id}.vtt", allowed_dir=OUTPUT_DIR)

    srt_content = segments_to_srt(segments)
    srt_path.write_text(srt_content, encoding="utf-8")

    vtt_content = segments_to_vtt(segments)
    vtt_path.write_text(vtt_content, encoding="utf-8")

    task["segments"] = len(segments)
    logger.info(f"EDIT [{task_id[:8]}] Subtitles updated: {len(segments)} segments")

    return {"message": "Subtitles updated", "segments": len(segments)}


@router.put("/subtitles/{task_id}/{segment_index}")
async def edit_subtitle(task_id: str, segment_index: int, request: Request):
    """Edit the text of a specific subtitle segment."""
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    task = state.tasks[task_id]
    if task.get("status") != "done":
        raise HTTPException(400, "Task not yet complete")

    body = await request.json()
    new_text = str(body.get("text", "")).strip()
    if not new_text:
        raise HTTPException(400, "Text cannot be empty")

    json_path = safe_path(OUTPUT_DIR / f"{task_id}.json", allowed_dir=OUTPUT_DIR)
    if not json_path.exists():
        raise HTTPException(404, "Output file not found")

    with open(json_path, "r", encoding="utf-8") as f:
        segments = json.load(f)

    if segment_index < 0 or segment_index >= len(segments):
        raise HTTPException(400, f"Segment index out of range (0-{len(segments) - 1})")

    old_text = segments[segment_index].get("text", "")
    segments[segment_index]["text"] = new_text

    # Write back JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    # Regenerate SRT and VTT
    srt_path = safe_path(OUTPUT_DIR / f"{task_id}.srt", allowed_dir=OUTPUT_DIR)
    vtt_path = safe_path(OUTPUT_DIR / f"{task_id}.vtt", allowed_dir=OUTPUT_DIR)
    srt_path.write_text(segments_to_srt(segments), encoding="utf-8")
    vtt_path.write_text(segments_to_vtt(segments), encoding="utf-8")

    logger.info(f"EDIT [{task_id[:8]}] Segment {segment_index} text changed")
    return {"message": "Segment updated", "segment_index": segment_index, "old_text": old_text, "new_text": new_text}


def _parse_srt(content: str) -> list[dict]:
    """Parse SRT content back into segment dicts."""
    segments = []
    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        # Line 0: index, Line 1: timestamps, Line 2+: text
        timestamp_line = lines[1]
        parts = timestamp_line.split(" --> ")
        if len(parts) != 2:
            continue
        start = _parse_timestamp(parts[0].strip())
        end = _parse_timestamp(parts[1].strip())
        text = "\n".join(lines[2:]).strip()
        segments.append({"start": start, "end": end, "text": text})
    return segments


def _parse_timestamp(ts: str) -> float:
    """Parse SRT timestamp (HH:MM:SS,mmm) to seconds."""
    ts = ts.replace(",", ".")
    parts = ts.split(":")
    if len(parts) != 3:
        return 0.0
    h, m, s = parts
    return int(h) * 3600 + int(m) * 60 + float(s)
