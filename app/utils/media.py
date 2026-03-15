"""Media file utilities: ffprobe, ffmpeg, file operations."""

import json
import logging
import subprocess
import time
from pathlib import Path

logger = logging.getLogger("subtitle-generator")

# Security: restrict ffmpeg protocols to prevent SSRF via crafted media files
FFMPEG_PROTOCOL_WHITELIST = "file,pipe,crypto,data"
FFMPEG_TIMEOUT = 300  # 5 minutes max for ffmpeg operations


def get_audio_duration(file_path: Path) -> float:
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(file_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            fmt = info.get("format", {})
            duration = float(fmt.get("duration", 0))
            streams = info.get("streams", [])
            has_audio = False
            for s in streams:
                codec_type = s.get("codec_type", "?")
                codec_name = s.get("codec_name", "?")
                if codec_type == "audio":
                    has_audio = True
                    logger.debug(
                        f"PROBE Audio: codec={codec_name} sample_rate={s.get('sample_rate')} "
                        f"channels={s.get('channels')} bitrate={s.get('bit_rate')}"
                    )
                elif codec_type == "video":
                    logger.debug(
                        f"PROBE Video: codec={codec_name} {s.get('width')}x{s.get('height')} "
                        f"fps={s.get('r_frame_rate')}"
                    )
            logger.debug(
                f"PROBE Duration: {duration:.2f}s, Format: {fmt.get('format_name')}, "
                f"Size: {fmt.get('size')} bytes, Has audio: {has_audio}"
            )
            return duration
    except subprocess.TimeoutExpired:
        logger.error(f"PROBE Timeout for {file_path}")
    except Exception as e:
        logger.error(f"PROBE Failed for {file_path}: {e}")
    return 0.0


def extract_audio(video_path: Path, audio_path: Path, threads: int = 0, task_id: str = ""):
    """Extract audio to 16kHz mono WAV with security restrictions.

    If task_id is provided, stores the subprocess in state.tasks[task_id]["_subprocess"]
    so it can be killed immediately on critical state.
    """
    cmd = [
        "ffmpeg",
        "-protocol_whitelist",
        FFMPEG_PROTOCOL_WHITELIST,
    ]
    if threads > 0:
        cmd += ["-threads", str(threads)]
    cmd += [
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-y",
        str(audio_path),
    ]
    logger.debug(f"FFMPEG Running: {' '.join(cmd)}")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Store process ref for force-kill
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
        # Clear subprocess ref
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

            task = state.tasks.get(task_id)
            if task and task.get("cancel_requested"):
                from app.exceptions import CriticalAbortError

                if state.system_critical:
                    reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "Unknown"
                    raise CriticalAbortError(f"ffmpeg killed — system critical: {reasons}")
        # Extract the actual error from stderr (skip ffmpeg banner/config noise)
        error_lines = [
            line
            for line in stderr.strip().splitlines()
            if not line.startswith(("  ", "ffmpeg version", "  built with", "  configuration:", "  lib"))
            and line.strip()
        ]
        error_msg = "\n".join(error_lines[-5:]) if error_lines else stderr[-200:]
        logger.error(f"FFMPEG Failed (exit={proc.returncode}, {elapsed:.1f}s): {error_msg}")
        raise RuntimeError(f"ffmpeg error (exit {proc.returncode}): {error_msg}")
    logger.info(f"FFMPEG Audio extracted in {elapsed:.1f}s -> {audio_path.name}")


def get_file_size(file_path: Path) -> int:
    try:
        return file_path.stat().st_size
    except Exception:
        return 0


def has_audio_stream(file_path: Path) -> bool:
    """Check if a file contains an audio stream (validates it's real media)."""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-select_streams", "a", str(file_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return len(info.get("streams", [])) > 0
    except Exception:
        pass
    return False
