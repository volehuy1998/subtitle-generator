"""Video processing pipeline: orchestrates probe -> extract -> load -> transcribe -> SRT."""

import logging
import threading
import time as _time
import traceback
from pathlib import Path

from app import state
from app.config import OUTPUT_DIR, MAX_AUDIO_DURATION
from app.exceptions import CancelledError, CriticalAbortError
from app.logging_setup import log_task_event
from app.services.gpu import check_vram_for_model
from app.services.model_manager import get_model, get_compute_type
from app.services.sse import emit_event
from app.services.transcription import transcribe_with_progress
from app.utils.formatting import format_bytes, format_time_display
from app.utils.media import get_audio_duration, get_file_size, extract_audio
from app.utils.srt import segments_to_srt, segments_to_vtt, segments_to_json
from app.utils.subtitle_format import format_segments_with_linebreaks, validate_timing
from app.services.diarization import is_diarization_available, diarize_audio, assign_speakers_to_segments
from app.services.analytics import record_completion, record_failure, record_cancellation, record_error_category
from app.routes.metrics import inc
from profiler import StepTimer, PipelineSummary, ResourceMonitor
from app.services.task_backend import get_task_backend

logger = logging.getLogger("subtitle-generator")

# Tasks that failed to persist to DB — retried on next successful persist
_pending_db_persists: list[tuple[str, dict]] = []
_pending_lock = threading.Lock()


def _retry_pending_persists():
    """Try to persist any tasks that previously failed to write to DB."""
    if not _pending_db_persists:
        return
    backend = get_task_backend()
    try:
        from app.db.task_backend_db import DatabaseTaskBackend
        if not isinstance(backend, DatabaseTaskBackend):
            return
    except ImportError:
        return

    with _pending_lock:
        pending = list(_pending_db_persists)

    succeeded = []
    for task_id, task_data in pending:
        try:
            backend.schedule_persist(task_id, task_data)
            succeeded.append((task_id, task_data))
            logger.info(f"TASK [{task_id[:8]}] DB persist retry succeeded")
        except Exception:
            break  # DB probably still down

    if succeeded:
        with _pending_lock:
            for item in succeeded:
                if item in _pending_db_persists:
                    _pending_db_persists.remove(item)


def _check_critical(task_id: str):
    """Abort the pipeline if the system has entered critical state."""
    if state.system_critical:
        reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "Unknown"
        raise CriticalAbortError(f"System critical — processing halted: {reasons}")


def _auto_embed_subtitles(task_id: str, video_path: Path, mode: str, language: str):
    """Auto-embed subtitles into the original video after transcription."""
    from app.services.subtitle_embed import soft_embed_subtitles, hard_burn_subtitles, SubtitleStyle, STYLE_PRESETS

    srt_path = OUTPUT_DIR / f"{task_id}.srt"
    if not srt_path.exists():
        logger.warning(f"TASK [{task_id[:8]}] Auto-embed skipped: no SRT file")
        return

    task = state.tasks.get(task_id, {})
    emit_event(task_id, "embed_progress", {"message": "Embedding subtitles into video...", "percent": 100})

    ext = video_path.suffix
    out_ext = ".mkv" if mode == "soft" and ext == ".mkv" else ".mp4"
    output_path = OUTPUT_DIR / f"embed_{task_id}{out_ext}"

    if mode == "hard":
        style = STYLE_PRESETS.get("youtube_white", SubtitleStyle())
        hard_burn_subtitles(video_path, srt_path, output_path, style, task_id)
    else:
        soft_embed_subtitles(video_path, srt_path, output_path, task_id, language=language)

    task["embedded_video"] = str(output_path.name)
    log_task_event(task_id, "auto_embed_complete", mode=mode, output=output_path.name)
    emit_event(task_id, "embed_done", {
        "message": f"Subtitles embedded ({mode} mode)",
        "download_url": f"/embed/download/{task_id}",
        "output": output_path.name,
        "mode": mode,
    })
    logger.info(f"TASK [{task_id[:8]}] Auto-embed complete: {output_path.name}")


def _persist_task(task_id: str, task: dict):
    """Persist task to DB (mandatory). Queues for retry if DB write fails."""
    # First, try to flush any previously failed persists
    _retry_pending_persists()

    backend = get_task_backend()
    try:
        from app.db.task_backend_db import DatabaseTaskBackend
        if isinstance(backend, DatabaseTaskBackend):
            backend.schedule_persist(task_id, task)
            return
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"TASK [{task_id[:8]}] DB persist failed, queued for retry: {e}")
        with _pending_lock:
            _pending_db_persists.append((task_id, dict(task)))
    # Fallback to legacy JSON persistence
    state.save_task_history()


def process_video(task_id: str, video_path: Path, model_size: str, device: str,
                   language: str = "auto", word_timestamps: bool = False,
                   initial_prompt: str = "", diarize: bool = False,
                   num_speakers: int = None, max_line_chars: int = 42,
                   translate_to_english: bool = False,
                   auto_embed: str = "", translate_to: str = ""):
    """Main processing pipeline. Runs in a background thread."""
    # Acquire concurrency semaphore
    sem = state.get_task_semaphore()
    sem.acquire()

    audio_path = video_path.with_suffix(".wav")

    pause_event = threading.Event()
    pause_event.set()
    # Ensure task exists in local state (may come from Redis on worker nodes)
    if task_id not in state.tasks:
        state.tasks[task_id] = {"status": "queued", "percent": 0, "message": "Starting..."}
    task = state.tasks[task_id]
    task["pause_event"] = pause_event
    task["cancel_requested"] = False
    task["_thread_id"] = threading.current_thread().ident
    task["device"] = device.upper()
    task["model_size"] = model_size
    task["language_requested"] = language
    task["word_timestamps"] = word_timestamps
    task["diarize"] = diarize
    task["segments_preview"] = []

    # Track whether input is a video file (for deferred embed)
    VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".webm", ".mov"}
    is_video_file = video_path.suffix.lower() in VIDEO_EXTENSIONS
    task["is_video"] = is_video_file

    pipeline = PipelineSummary(task_id, task.get("filename", "unknown"), model_size, device)
    monitor = ResourceMonitor(task_id, interval=2.0)
    monitor.start()

    logger.info(f"TASK [{task_id[:8]}] Pipeline started: file={task.get('filename')} model={model_size} device={device}")
    log_task_event(task_id, "pipeline_start", filename=task.get("filename"), model=model_size, device=device)
    task["current_step"] = 0
    emit_event(task_id, "pipeline_start", {"status": "queued", "model": model_size, "device": device.upper()})
    emit_event(task_id, "step_change", {"step": 0, "status": "uploading", "percent": 0, "message": "Analysing file..."})

    # VRAM warning
    if device == "cuda":
        vram_check = check_vram_for_model(model_size)
        if not vram_check.get("fits", True):
            logger.warning(
                f"TASK [{task_id[:8]}] VRAM WARNING: {model_size} requires ~{vram_check.get('required_gb')}GB "
                f"but only {vram_check.get('free_gb')}GB free."
            )
            log_task_event(task_id, "vram_warning", **vram_check)
            emit_event(task_id, "warning", {
                "message": f"Model '{model_size}' may not fit in VRAM ({vram_check.get('free_gb')}GB free, ~{vram_check.get('required_gb')}GB needed).",
            })

    try:
        # Step 1: Probe
        with StepTimer(task_id, "probe", task_log_func=log_task_event) as step_probe:
            duration = get_audio_duration(video_path)
            file_size = get_file_size(video_path)
            duration_str = format_time_display(duration) if duration > 0 else "unknown"
            task["duration"] = duration_str
            task["file_size"] = file_size
            task["file_size_fmt"] = format_bytes(file_size)
            pipeline.file_size = file_size
            pipeline.audio_duration = duration
        pipeline.record_step("probe", step_probe.elapsed)
        emit_event(task_id, "probe_done", {
            "duration": duration_str,
            "file_size": file_size,
            "file_size_fmt": format_bytes(file_size),
        })

        # Validate duration
        if duration > MAX_AUDIO_DURATION:
            raise ValueError(
                f"Audio too long ({format_time_display(duration)}). "
                f"Maximum is {format_time_display(MAX_AUDIO_DURATION)}."
            )
        if duration <= 0:
            logger.warning(f"TASK [{task_id[:8]}] Could not determine audio duration, proceeding anyway")

        if task.get("cancel_requested"):
            raise CancelledError("Task cancelled by user")
        _check_critical(task_id)

        # Step 2: Extract audio
        task["status"] = "extracting"
        task["current_step"] = 1
        task["percent"] = 5
        task["message"] = f"Extracting audio ({duration_str}, {format_bytes(file_size)})..."
        task["step_timing"] = {"upload": round(step_probe.elapsed, 2)}
        log_task_event(task_id, "step_start", step=1, name="extract", status="extracting")
        emit_event(task_id, "step_change", {
            "step": 1, "status": "extracting", "percent": 5, "message": task["message"],
            "step_timing": task["step_timing"],
            "step_started_at": _time.time(),
        })

        with StepTimer(task_id, "extract_audio", task_log_func=log_task_event) as step_extract:
            extract_audio(video_path, audio_path, task_id=task_id)
            audio_size = get_file_size(audio_path)
            task["audio_size_fmt"] = format_bytes(audio_size)
            pipeline.audio_size = audio_size
        pipeline.record_step("extract_audio", step_extract.elapsed)
        emit_event(task_id, "extract_done", {
            "audio_size": audio_size,
            "audio_size_fmt": format_bytes(audio_size),
            "extract_time_sec": round(step_extract.elapsed, 2),
        })

        if task.get("cancel_requested"):
            raise CancelledError("Task cancelled by user")
        _check_critical(task_id)

        task["percent"] = 15
        task["message"] = f"Audio extracted ({format_bytes(audio_size)}). Loading model..."

        # Step 3: Load model → Transcribe
        task["status"] = "transcribing"
        task["current_step"] = 2
        compute_type = get_compute_type(device, model_size)
        task["message"] = f"Loading {model_size} model on {device.upper()} ({compute_type})..."
        task["step_timing"] = {"upload": round(step_probe.elapsed, 2), "extract": round(step_extract.elapsed, 2)}
        log_task_event(task_id, "step_start", step=2, name="transcribe", status="transcribing",
                       model=model_size, device=device)
        emit_event(task_id, "step_change", {
            "step": 2, "status": "transcribing", "percent": 15, "message": task["message"],
            "step_timing": task["step_timing"],
            "step_started_at": _time.time(),
            "model_size": model_size,
            "device": device.upper(),
        })

        with StepTimer(task_id, "model_load", task_log_func=log_task_event) as step_model:
            m = get_model(model_size, device)
        pipeline.record_step("model_load", step_model.elapsed)
        emit_event(task_id, "model_loaded", {
            "model": model_size, "device": device.upper(),
            "compute_type": compute_type, "load_time_sec": round(step_model.elapsed, 2),
        })

        if task.get("cancel_requested"):
            raise CancelledError("Task cancelled by user")
        _check_critical(task_id)

        task["message"] = f"Transcribing on {device.upper()} ({model_size} model, {compute_type})..."

        # Step 4: Transcribe
        with StepTimer(task_id, "transcribe", task_log_func=log_task_event) as step_transcribe:
            result = transcribe_with_progress(
                m, str(audio_path), task_id, device, model_size, duration,
                language, word_timestamps=word_timestamps, initial_prompt=initial_prompt,
                translate_to_english=translate_to_english,
            )
        pipeline.record_step("transcribe", step_transcribe.elapsed)

        segments = result["segments"]

        # Step 4b: Speaker diarization (optional)
        if diarize and is_diarization_available()["available"]:
            task["message"] = "Identifying speakers..."
            emit_event(task_id, "step_change", {"status": "diarizing", "message": task["message"]})
            with StepTimer(task_id, "diarize", task_log_func=log_task_event) as step_diarize:
                speaker_turns = diarize_audio(audio_path, task_id, num_speakers=num_speakers)
                segments = assign_speakers_to_segments(segments, speaker_turns)
                task["speakers"] = len(set(t["speaker"] for t in speaker_turns)) if speaker_turns else 0
            pipeline.record_step("diarize", step_diarize.elapsed)

        # Step 4c: Apply line-breaking rules
        segments = format_segments_with_linebreaks(segments, max_chars=max_line_chars)

        # Step 4d: Translation (optional, for non-English targets)
        step_translate_elapsed = 0
        detected_lang = result.get("language", "unknown")
        if translate_to and translate_to != "en" and translate_to != detected_lang:
            from app.services.translation import translate_segments as do_translate
            task["status"] = "translating"
            task["message"] = f"Translating subtitles to {translate_to}..."
            emit_event(task_id, "step_change", {
                "step": 2, "status": "translating",
                "percent": 90, "message": task["message"],
            })
            with StepTimer(task_id, "translate", task_log_func=log_task_event) as step_translate:
                segments = do_translate(segments, detected_lang, translate_to, task_id)
            step_translate_elapsed = step_translate.elapsed
            pipeline.record_step("translate", step_translate_elapsed)
            # Re-apply line-breaking on translated text (different word lengths)
            segments = format_segments_with_linebreaks(segments, max_chars=max_line_chars)
            task["translated_to"] = translate_to
            # Update live preview with translated segments
            from app.utils.formatting import format_time_short
            for seg in segments:
                emit_event(task_id, "segment", {"segment": {
                    "start": seg["start"], "end": seg["end"], "text": seg["text"],
                    "start_fmt": format_time_short(seg["start"]),
                    "end_fmt": format_time_short(seg["end"]),
                    "speaker": seg.get("speaker"),
                }, "translated": True})

        # Validate timing quality
        timing_issues = 0
        for seg in segments:
            diag = validate_timing(seg["start"], seg["end"], seg["text"])
            if not diag["valid"]:
                timing_issues += 1
        if timing_issues > 0:
            logger.info(f"TASK [{task_id[:8]}] Subtitle quality: {timing_issues}/{len(segments)} segments have timing issues")

        result["segments"] = segments
        num_segments = len(segments)
        language = result.get("language", "unknown")
        transcribe_time = step_transcribe.elapsed
        speed_factor = duration / transcribe_time if transcribe_time > 0 else 0

        tx_profiler = task.get("transcription_profiler")
        if tx_profiler:
            tx_summary = tx_profiler.summary()
            pipeline.transcription_summary = tx_summary
            log_task_event(task_id, "transcription_profile", **tx_summary)

        log_task_event(
            task_id, "transcription_complete",
            segments=num_segments, language=language,
            transcribe_time_sec=round(transcribe_time, 2),
            speed_factor=round(speed_factor, 2),
            audio_duration_sec=round(duration, 2),
        )

        if task.get("cancel_requested"):
            raise CancelledError("Task cancelled by user")
        _check_critical(task_id)

        # Step 5: Generate SRT (finalize)
        task["status"] = "writing"
        task["current_step"] = 3
        task["percent"] = 95
        task["message"] = "Generating subtitle file..."
        task["step_timing"] = {
            "upload": round(step_probe.elapsed, 2),
            "extract": round(step_extract.elapsed, 2),
            "transcribe": round(step_transcribe.elapsed, 2),
        }
        log_task_event(task_id, "step_start", step=3, name="finalize", status="writing",
                       segments=num_segments, language=language)
        emit_event(task_id, "step_change", {
            "step": 3, "status": "writing", "percent": 95, "message": "Generating subtitle file...",
            "step_timing": task["step_timing"],
            "step_started_at": _time.time(),
        })

        has_speakers = any("speaker" in s for s in result["segments"])
        has_words = any("words" in s for s in result["segments"])

        with StepTimer(task_id, "write_srt", task_log_func=log_task_event) as step_srt:
            srt_content = segments_to_srt(result["segments"], include_speakers=has_speakers)
            srt_path = OUTPUT_DIR / f"{task_id}.srt"
            srt_path.write_text(srt_content, encoding="utf-8")

            vtt_content = segments_to_vtt(result["segments"], include_speakers=has_speakers)
            vtt_path = OUTPUT_DIR / f"{task_id}.vtt"
            vtt_path.write_text(vtt_content, encoding="utf-8")

            # Save JSON with word-level data if available
            if has_words or has_speakers:
                json_content = segments_to_json(result["segments"])
                json_path = OUTPUT_DIR / f"{task_id}.json"
                json_path.write_text(json_content, encoding="utf-8")

            srt_size = get_file_size(srt_path)
            pipeline.srt_size = srt_size
        pipeline.record_step("write_srt", step_srt.elapsed)

        # Upload outputs to S3 if configured
        from app.config import STORAGE_BACKEND
        if STORAGE_BACKEND == "s3":
            try:
                from app.services.storage import get_storage
                storage = get_storage()
                for out_ext in ("srt", "vtt", "json"):
                    out_file = OUTPUT_DIR / f"{task_id}.{out_ext}"
                    if out_file.exists():
                        storage.save_output_from_path(out_file.name, out_file)
                logger.info(f"TASK [{task_id[:8]}] Outputs uploaded to S3")
            except Exception as e:
                logger.error(f"TASK [{task_id[:8]}] S3 upload failed: {e}")

        # Step 6: Done
        monitor.stop()
        monitor_summary = monitor.summary()
        if monitor_summary:
            log_task_event(task_id, "resource_monitor", **monitor_summary)

        pipeline_summary = pipeline.finalize(status="complete")
        pipeline_summary.pop("task_id", None)
        log_task_event(task_id, "pipeline_summary", **pipeline_summary)

        task["status"] = "done"
        task["percent"] = 100
        done_suffix = ""
        if translate_to and translate_to != "en" and translate_to != detected_lang:
            done_suffix = f", translated to {translate_to}"
        task["message"] = (
            f"Done! {num_segments} subtitles generated "
            f"(language: {language}, {device.upper()}, took {format_time_display(transcribe_time)}{done_suffix})"
        )
        task["segments"] = num_segments
        task["language"] = language
        final_step_timing = {
            "upload": round(step_probe.elapsed, 2),
            "extract": round(step_extract.elapsed, 2),
            "transcribe": round(step_transcribe.elapsed, 2),
            "finalize": round(step_srt.elapsed, 2),
        }
        if step_translate_elapsed > 0:
            final_step_timing["translate"] = round(step_translate_elapsed, 2)
        task["step_timing"] = final_step_timing

        done_data = {
            "status": "done", "percent": 100, "message": task["message"],
            "segments": num_segments, "language": language,
            "total_time_sec": round(pipeline_summary.get("total_time_sec", 0), 2),
            "speed_factor": round(speed_factor, 2),
            "step_timings": task["step_timing"],
            "is_video": is_video_file,
        }
        if task.get("translated_to"):
            done_data["translated_to"] = task["translated_to"]
        emit_event(task_id, "done", done_data)

        # Record analytics
        total_time = pipeline_summary.get("total_time_sec", 0)
        record_completion(total_time, model=model_size)
        inc("transcriptions_completed")

        audio_path.unlink(missing_ok=True)

        # Auto-embed subtitles if requested
        if auto_embed and video_path.exists():
            try:
                _auto_embed_subtitles(task_id, video_path, auto_embed, language)
            except Exception as e:
                logger.error(f"TASK [{task_id[:8]}] Auto-embed failed: {e}")
                emit_event(task_id, "embed_error", {"message": f"Auto-embed failed: {e}"})
            finally:
                video_path.unlink(missing_ok=True)
        elif is_video_file and video_path.exists():
            # Preserve video for deferred embed (user can embed after reviewing subtitles)
            task["preserved_video"] = str(video_path.name)
            logger.info(f"TASK [{task_id[:8]}] Video preserved for deferred embed: {video_path.name}")
        else:
            video_path.unlink(missing_ok=True)

        _persist_task(task_id, task)

    except CancelledError:
        monitor.stop()
        pipeline_summary = pipeline.finalize(status="cancelled")
        pipeline_summary.pop("task_id", None)
        log_task_event(task_id, "pipeline_summary", **pipeline_summary)
        task["status"] = "cancelled"
        # Keep last known percent so task queue shows how far it got
        task["message"] = "Task cancelled by user."
        logger.warning(f"TASK [{task_id[:8]}] CANCELLED")
        emit_event(task_id, "cancelled", {"status": "cancelled", "message": "Task cancelled by user."})
        record_cancellation()
        inc("transcriptions_cancelled")
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
        _persist_task(task_id, task)

    except CriticalAbortError as e:
        monitor.stop()
        pipeline_summary = pipeline.finalize(status="aborted")
        pipeline_summary.pop("task_id", None)
        log_task_event(task_id, "pipeline_summary", **pipeline_summary)
        reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "System critical"
        task["status"] = "error"
        # Keep last known percent so task queue shows how far it got
        task["message"] = f"Processing halted — {reasons}"
        logger.error(f"TASK [{task_id[:8]}] CRITICAL ABORT: {e}")
        log_task_event(task_id, "critical_abort", error=str(e), reasons=state.system_critical_reasons)
        emit_event(task_id, "critical_abort", {
            "status": "error",
            "message": task["message"],
            "critical": True,
            "reasons": list(state.system_critical_reasons),
        })
        record_failure()
        record_error_category("CriticalAbort")
        inc("transcriptions_failed")
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
        _persist_task(task_id, task)

    except Exception as e:
        monitor.stop()
        pipeline_summary = pipeline.finalize(status="error")
        pipeline_summary.pop("task_id", None)
        log_task_event(task_id, "pipeline_summary", **pipeline_summary)
        task["status"] = "error"
        # Keep last known percent so task queue shows how far it got
        task["message"] = str(e)
        logger.error(f"TASK [{task_id[:8]}] ERROR: {e}\n{traceback.format_exc()}")
        log_task_event(task_id, "error", error=str(e), traceback=traceback.format_exc())
        emit_event(task_id, "error", {"status": "error", "message": str(e)})
        record_failure()
        record_error_category(type(e).__name__)
        inc("transcriptions_failed")
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
        _persist_task(task_id, task)

    finally:
        task.pop("_thread_id", None)
        sem.release()
