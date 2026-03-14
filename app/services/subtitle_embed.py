"""Subtitle embedding into video files with customizable styling.

Supports two modes:
  1. Soft embed (mux) - Adds subtitle track to container (MKV/MP4). Lossless, fast.
  2. Hard burn - Renders subtitles directly onto video frames. Customizable style.

Style options mirror YouTube subtitle customization:
  - Font family, size, color, opacity
  - Background color and opacity
  - Outline/shadow color and thickness
  - Position (top, center, bottom)
  - Bold, italic
"""

import logging
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from app.logging_setup import log_task_event
from app.utils.media import FFMPEG_PROTOCOL_WHITELIST, FFMPEG_TIMEOUT

logger = logging.getLogger("subtitle-generator")


def _sanitize_font_name(name: str) -> str:
    """Strip dangerous characters from font name. Only allow alphanumeric, spaces, dash, underscore."""
    sanitized = re.sub(r"[^a-zA-Z0-9 _-]", "", name)
    return sanitized.strip() or "Arial"


@dataclass
class SubtitleStyle:
    """YouTube-like subtitle styling options."""

    font_name: str = "Arial"
    font_size: int = 24
    font_color: str = "&HFFFFFF"  # ASS format: &HBBGGRR (white)
    font_opacity: float = 1.0  # 0.0 - 1.0
    bold: bool = False
    italic: bool = False
    outline_color: str = "&H000000"  # Black outline
    outline_width: float = 2.0
    shadow_offset: float = 1.0
    shadow_color: str = "&H000000"
    background_color: str = "&H000000"  # Box background
    background_opacity: float = 0.5
    position: str = "bottom"  # top, center, bottom
    margin_v: int = 30  # Vertical margin from edge

    def to_ass_style(self) -> str:
        """Convert to ASS subtitle style string for ffmpeg subtitles filter."""
        # ASS alpha: 00=opaque, FF=transparent
        font_alpha = format(int((1 - self.font_opacity) * 255), "02X")
        bg_alpha = format(int((1 - self.background_opacity) * 255), "02X")

        # Position alignment (ASS alignment: 1-3 bottom, 4-6 middle, 7-9 top, 2/5/8=center)
        alignment = {"bottom": 2, "center": 5, "top": 8}.get(self.position, 2)

        safe_font = _sanitize_font_name(self.font_name)
        parts = [
            f"FontName={safe_font}",
            f"FontSize={self.font_size}",
            f"PrimaryColour=&H{font_alpha}{self.font_color[2:]}",
            f"OutlineColour=&H00{self.outline_color[2:]}",
            f"BackColour=&H{bg_alpha}{self.shadow_color[2:]}",
            f"Bold={-1 if self.bold else 0}",
            f"Italic={-1 if self.italic else 0}",
            f"Outline={self.outline_width}",
            f"Shadow={self.shadow_offset}",
            f"Alignment={alignment}",
            f"MarginV={self.margin_v}",
            "BorderStyle=3" if self.background_opacity > 0 else "BorderStyle=1",
        ]
        return ",".join(parts)

    def to_force_style(self) -> str:
        """Generate force_style parameter for ffmpeg subtitles filter."""
        return f"'force_style={self.to_ass_style()}'"


def soft_embed_subtitles(
    video_path: Path,
    subtitle_path: Path,
    output_path: Path,
    task_id: str = "",
    language: str = "eng",
) -> Path:
    """Mux subtitles into video container as a selectable track. Fast, lossless."""
    logger.info(f"EMBED [{task_id[:8]}] Soft embed: {subtitle_path.name} -> {output_path.name}")
    t0 = time.time()

    # Determine subtitle codec based on container
    ext = output_path.suffix.lower()
    sub_codec = "srt" if ext == ".mkv" else "mov_text"  # mov_text for MP4

    cmd = [
        "ffmpeg",
        "-protocol_whitelist",
        FFMPEG_PROTOCOL_WHITELIST,
        "-i",
        str(video_path),
        "-i",
        str(subtitle_path),
        "-c",
        "copy",
        "-c:s",
        sub_codec,
        "-metadata:s:s:0",
        f"language={language}",
        "-metadata:s:s:0",
        "title=Subtitles",
        "-y",
        str(output_path),
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Store process ref for force-kill on critical state
    if task_id:
        from app import state

        task = state.tasks.get(task_id)
        if task:
            task["_subprocess"] = proc

    try:
        stdout, stderr = proc.communicate(timeout=FFMPEG_TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise
    finally:
        if task_id:
            from app import state

            task = state.tasks.get(task_id)
            if task:
                task.pop("_subprocess", None)

    elapsed = time.time() - t0

    if proc.returncode != 0:
        # Check if killed by critical state
        if task_id:
            from app import state

            if state.system_critical:
                from app.exceptions import CriticalAbortError

                reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "Unknown"
                raise CriticalAbortError(f"Embed killed — system critical: {reasons}")
        logger.error(f"EMBED [{task_id[:8]}] Soft embed failed ({elapsed:.1f}s): {stderr[:500]}")
        raise RuntimeError(f"Subtitle embedding failed: {stderr[:300]}")

    logger.info(f"EMBED [{task_id[:8]}] Soft embed done in {elapsed:.1f}s -> {output_path.name}")
    if task_id:
        log_task_event(task_id, "subtitle_embed", mode="soft", elapsed_sec=round(elapsed, 2))
    return output_path


def hard_burn_subtitles(
    video_path: Path,
    subtitle_path: Path,
    output_path: Path,
    style: SubtitleStyle = None,
    task_id: str = "",
) -> Path:
    """Burn subtitles directly onto video frames with custom styling. Re-encodes video."""
    if style is None:
        style = SubtitleStyle()

    logger.info(
        f"EMBED [{task_id[:8]}] Hard burn: {subtitle_path.name} -> {output_path.name} (font={style.font_name}, size={style.font_size})"
    )
    t0 = time.time()

    # Build subtitles filter with styling
    # Escape colons and backslashes in path for ffmpeg filter
    sub_path_escaped = str(subtitle_path).replace("\\", "/").replace(":", "\\:")
    force_style = style.to_ass_style()
    vf = f"subtitles='{sub_path_escaped}':force_style='{force_style}'"

    cmd = [
        "ffmpeg",
        "-protocol_whitelist",
        FFMPEG_PROTOCOL_WHITELIST,
        "-i",
        str(video_path),
        "-vf",
        vf,
        "-c:a",
        "copy",
        "-y",
        str(output_path),
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Store process ref for force-kill on critical state
    if task_id:
        from app import state

        task = state.tasks.get(task_id)
        if task:
            task["_subprocess"] = proc

    try:
        stdout, stderr = proc.communicate(timeout=FFMPEG_TIMEOUT * 2)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise
    finally:
        if task_id:
            from app import state

            task = state.tasks.get(task_id)
            if task:
                task.pop("_subprocess", None)

    elapsed = time.time() - t0

    if proc.returncode != 0:
        # Check if killed by critical state
        if task_id:
            from app import state

            if state.system_critical:
                from app.exceptions import CriticalAbortError

                reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "Unknown"
                raise CriticalAbortError(f"Embed killed — system critical: {reasons}")
        logger.error(f"EMBED [{task_id[:8]}] Hard burn failed ({elapsed:.1f}s): {stderr[:500]}")
        raise RuntimeError(f"Subtitle burn failed: {stderr[:300]}")

    logger.info(f"EMBED [{task_id[:8]}] Hard burn done in {elapsed:.1f}s -> {output_path.name}")
    if task_id:
        log_task_event(
            task_id,
            "subtitle_embed",
            mode="hard",
            elapsed_sec=round(elapsed, 2),
            font=style.font_name,
            size=style.font_size,
            position=style.position,
        )
    return output_path


# YouTube-style presets
STYLE_PRESETS = {
    "default": SubtitleStyle(),
    "youtube_white": SubtitleStyle(
        font_name="Arial",
        font_size=24,
        font_color="&HFFFFFF",
        background_color="&H000000",
        background_opacity=0.75,
        outline_width=0,
        shadow_offset=0,
    ),
    "youtube_yellow": SubtitleStyle(
        font_name="Arial",
        font_size=24,
        font_color="&H00FFFF",
        background_color="&H000000",
        background_opacity=0.75,
        outline_width=0,
        shadow_offset=0,
    ),
    "cinema": SubtitleStyle(
        font_name="Arial",
        font_size=28,
        font_color="&HFFFFFF",
        outline_color="&H000000",
        outline_width=3,
        shadow_offset=2,
        background_opacity=0,
    ),
    "large_bold": SubtitleStyle(
        font_name="Arial",
        font_size=36,
        font_color="&HFFFFFF",
        bold=True,
        outline_width=3,
        background_opacity=0,
    ),
    "top_position": SubtitleStyle(
        font_name="Arial",
        font_size=24,
        font_color="&HFFFFFF",
        position="top",
        margin_v=20,
        background_opacity=0.5,
    ),
}
