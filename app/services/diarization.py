"""Speaker diarization service using pyannote.audio (optional dependency).

Identifies who is speaking in each segment. Gracefully degrades if
pyannote is not installed or HuggingFace token is not configured.

Requires:
  pip install pyannote.audio
  Set HF_TOKEN environment variable with a HuggingFace token that has
  access to pyannote/speaker-diarization-3.1 model.
"""

import logging
import os
import time
from pathlib import Path
from typing import Optional

from app.logging_setup import log_task_event

logger = logging.getLogger("subtitle-generator")

# Check if pyannote is available
_pyannote_available = False
try:
    from pyannote.audio import Pipeline as PyannotePipeline  # noqa: F401

    _pyannote_available = True
except ImportError:
    pass

# Cached pipeline instance
_diarization_pipeline = None
_pipeline_lock = None


def is_diarization_available() -> dict:
    """Check if speaker diarization is available and configured."""
    hf_token = os.environ.get("HF_TOKEN", "")
    return {
        "available": _pyannote_available and bool(hf_token),
        "pyannote_installed": _pyannote_available,
        "hf_token_set": bool(hf_token),
        "reason": (
            "Ready"
            if _pyannote_available and hf_token
            else "pyannote.audio not installed"
            if not _pyannote_available
            else "HF_TOKEN environment variable not set"
        ),
    }


def _get_pipeline():
    """Get or create the diarization pipeline (singleton)."""
    global _diarization_pipeline, _pipeline_lock
    import threading

    if _pipeline_lock is None:
        _pipeline_lock = threading.Lock()

    with _pipeline_lock:
        if _diarization_pipeline is not None:
            return _diarization_pipeline

        hf_token = os.environ.get("HF_TOKEN", "")
        if not hf_token:
            raise RuntimeError("HF_TOKEN not set. Required for pyannote speaker diarization.")

        logger.info("DIARIZE Loading pyannote speaker diarization pipeline...")
        t0 = time.time()

        import torch
        from pyannote.audio import Pipeline as PyannotePipeline

        pipeline = PyannotePipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token,
        )

        # Use GPU if available
        if torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
            logger.info("DIARIZE Pipeline loaded on GPU")
        else:
            logger.info("DIARIZE Pipeline loaded on CPU")

        elapsed = time.time() - t0
        logger.info(f"DIARIZE Pipeline loaded in {elapsed:.1f}s")
        _diarization_pipeline = pipeline
        return pipeline


def diarize_audio(
    audio_path: Path,
    task_id: str = "",
    num_speakers: Optional[int] = None,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
) -> list:
    """Run speaker diarization on audio file.

    Returns list of speaker turns:
    [{"start": float, "end": float, "speaker": str}, ...]
    """
    status = is_diarization_available()
    if not status["available"]:
        logger.warning(f"DIARIZE [{task_id[:8]}] Skipped: {status['reason']}")
        return []

    logger.info(f"DIARIZE [{task_id[:8]}] Starting speaker diarization...")
    t0 = time.time()
    log_task_event(task_id, "diarize_start")

    try:
        # Check critical state before starting expensive diarization
        from app import state
        from app.exceptions import CriticalAbortError

        if state.system_critical:
            reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "Unknown"
            raise CriticalAbortError(f"Diarization aborted — system critical: {reasons}")

        pipeline = _get_pipeline()

        # Build kwargs
        kwargs = {}
        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers
        elif min_speakers is not None or max_speakers is not None:
            if min_speakers is not None:
                kwargs["min_speakers"] = min_speakers
            if max_speakers is not None:
                kwargs["max_speakers"] = max_speakers

        diarization = pipeline(str(audio_path), **kwargs)

        # Check critical state after diarization completes (it's a single blocking call)
        if state.system_critical:
            reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "Unknown"
            raise CriticalAbortError(f"Diarization aborted — system critical: {reasons}")

        turns = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            turns.append(
                {
                    "start": round(turn.start, 3),
                    "end": round(turn.end, 3),
                    "speaker": speaker,
                }
            )

        elapsed = time.time() - t0
        unique_speakers = len(set(t["speaker"] for t in turns))
        logger.info(f"DIARIZE [{task_id[:8]}] Done: {len(turns)} turns, {unique_speakers} speakers in {elapsed:.1f}s")
        log_task_event(
            task_id, "diarize_complete", turns=len(turns), speakers=unique_speakers, elapsed_sec=round(elapsed, 2)
        )
        return turns

    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"DIARIZE [{task_id[:8]}] Failed after {elapsed:.1f}s: {e}")
        log_task_event(task_id, "diarize_error", error=str(e))
        return []


def assign_speakers_to_segments(segments: list, speaker_turns: list) -> list:
    """Assign speaker labels to transcription segments based on diarization turns.

    Uses overlap-based matching: each segment gets the speaker label
    of the turn with the greatest temporal overlap.
    """
    if not speaker_turns:
        return segments

    result = []
    for seg in segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        best_speaker = "UNKNOWN"
        best_overlap = 0

        for turn in speaker_turns:
            overlap_start = max(seg_start, turn["start"])
            overlap_end = min(seg_end, turn["end"])
            overlap = max(0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = turn["speaker"]

        enriched = dict(seg)
        enriched["speaker"] = best_speaker
        result.append(enriched)

    return result
