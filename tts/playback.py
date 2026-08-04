"""Serialized TTS jobs + blocking afplay (no overlap, no mid-speech kills)."""

from __future__ import annotations

import queue
import subprocess
import threading
from typing import Callable

_tts_lock = threading.Lock()
_job_queue: queue.Queue[tuple[Callable[[], bool] | None, threading.Event | None]] = (
    queue.Queue()
)
_worker_started = False
_cancel_event = threading.Event()


def _ensure_worker() -> None:
    global _worker_started
    with _tts_lock:
        if _worker_started:
            return
        _worker_started = True
        threading.Thread(
            target=_worker_loop, daemon=True, name="zesty-tts-playback"
        ).start()


def _worker_loop() -> None:
    while True:
        job, done = _job_queue.get()
        try:
            if job is None:
                return
            if _cancel_event.is_set():
                _cancel_event.clear()
            else:
                job()
        finally:
            if done is not None:
                done.set()
            _job_queue.task_done()


def stop_playback() -> None:
    """User-initiated stop — kill afplay and drop pending TTS jobs."""
    _cancel_event.set()
    subprocess.run(
        ["pkill", "afplay"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    while True:
        try:
            _job_queue.get_nowait()
            _job_queue.task_done()
        except queue.Empty:
            break


def play_file(path: str, *, wait: bool = True, timeout: float = 180.0) -> bool:
    """Play one audio file to completion. Caller must hold the TTS job slot."""
    try:
        subprocess.run(
            ["afplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return True
    except Exception as exc:
        print(f"[TTS] afplay failed: {exc}", flush=True)
        return False


def run_serialized(task: Callable[[], bool], *, wait: bool = True, timeout: float = 180.0) -> None:
    """Queue a full speak job so synthesis + playback never overlap."""
    _ensure_worker()
    done: threading.Event | None = threading.Event() if wait else None
    _job_queue.put((task, done))
    if done is not None:
        done.wait(timeout=timeout)
