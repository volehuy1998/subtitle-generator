"""Bulk export and sharing routes."""

import io
import logging
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request

from app import state
from app.config import OUTPUT_DIR

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Download"])

# Share links: share_id -> {task_id, created_at, expires_at}
_share_links: dict[str, dict] = {}


@router.get("/export/bulk")
async def bulk_export(
    request: Request,
    format: str = Query("srt", description="Subtitle format: srt, vtt, or json"),
    session_only: bool = Query(True, description="Export only your tasks"),
):
    """Download all completed subtitles as a ZIP archive.

    Includes all completed tasks (or only your session's tasks if session_only=true).
    """
    session_id = getattr(request.state, "session_id", "") if session_only else ""

    # Collect completed tasks
    files_to_zip = []
    for tid, t in state.tasks.items():
        if t.get("status") != "done":
            continue
        if session_only and t.get("session_id") != session_id:
            continue

        filename_base = Path(t.get("filename", "unknown")).stem
        subtitle_path = OUTPUT_DIR / f"{tid}.{format}"
        if subtitle_path.exists():
            files_to_zip.append((f"{filename_base}.{format}", subtitle_path))

    if not files_to_zip:
        raise HTTPException(404, "No completed subtitles found to export")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, path in files_to_zip:
            zf.write(path, name)

    zip_buffer.seek(0)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=subtitles_{format}.zip"},
    )


@router.post("/share/{task_id}")
async def create_share_link(task_id: str):
    """Create a temporary share link for downloading subtitles.

    The link is valid until the server restarts (in-memory storage).
    """
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    if state.tasks[task_id].get("status") != "done":
        raise HTTPException(400, "Task not completed yet")

    share_id = str(uuid.uuid4())[:12]
    _share_links[share_id] = {
        "task_id": task_id,
        "filename": state.tasks[task_id].get("filename", "unknown"),
    }

    logger.info(f"SHARE Created [{share_id}] for task [{task_id[:8]}]")
    return {
        "share_id": share_id,
        "share_url": f"/share/{share_id}/download",
        "task_id": task_id,
    }


@router.get("/share/{share_id}/download")
async def download_shared(
    share_id: str,
    format: str = Query("srt", description="srt, vtt, or json"),
):
    """Download subtitles via a share link (no authentication required)."""
    link = _share_links.get(share_id)
    if not link:
        raise HTTPException(404, "Share link not found or expired")

    task_id = link["task_id"]
    subtitle_path = OUTPUT_DIR / f"{task_id}.{format}"
    if not subtitle_path.exists():
        raise HTTPException(404, f"Subtitle file not found ({format})")

    # Security check
    if not str(subtitle_path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
        raise HTTPException(403, "Access denied")

    from fastapi.responses import FileResponse
    original_stem = Path(link["filename"]).stem
    media_types = {"srt": "text/plain", "vtt": "text/vtt", "json": "application/json"}
    return FileResponse(
        subtitle_path,
        filename=f"{original_stem}.{format}",
        media_type=media_types.get(format, "text/plain"),
    )


@router.get("/share/{share_id}/info")
async def share_info(share_id: str):
    """Get information about a share link."""
    link = _share_links.get(share_id)
    if not link:
        raise HTTPException(404, "Share link not found")
    return {
        "share_id": share_id,
        "task_id": link["task_id"],
        "filename": link["filename"],
    }


def get_active_shares() -> int:
    """Get count of active share links."""
    return len(_share_links)
