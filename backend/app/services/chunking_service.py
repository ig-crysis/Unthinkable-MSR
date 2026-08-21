"""Duration probing and silence-based audio splitting, via the system ffmpeg/ffprobe
binaries (subprocess — no extra Python audio package needed).
"""

import re
import subprocess
from pathlib import Path

from app.core.config import settings

_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)")
_SILENCE_START_RE = re.compile(r"silence_start:\s*([\d.]+)")
_SILENCE_END_RE = re.compile(r"silence_end:\s*([\d.]+)")


def get_duration_seconds(path: str) -> float | None:
    """Best-effort probe; returns None (never raises) if ffprobe is missing or fails."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True, text=True, timeout=30, check=False,
        )
        return float(result.stdout.strip())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def needs_chunking(file_size_bytes: int, duration_seconds: float | None) -> bool:
    if duration_seconds is not None and duration_seconds > settings.chunk_duration_threshold_min * 60:
        return True
    return file_size_bytes > settings.chunk_size_threshold_mb * 1024 * 1024


def _run_silencedetect(source_path: str) -> tuple[float | None, list[tuple[float, float]]]:
    result = subprocess.run(
        [
            "ffmpeg", "-i", source_path,
            "-af", "silencedetect=noise=-30dB:d=0.5",
            "-f", "null", "-",
        ],
        capture_output=True, text=True, timeout=600, check=False,
    )
    stderr = result.stderr

    duration = None
    if match := _DURATION_RE.search(stderr):
        h, m, s = match.groups()
        duration = int(h) * 3600 + int(m) * 60 + float(s)

    starts = [float(x) for x in _SILENCE_START_RE.findall(stderr)]
    ends = [float(x) for x in _SILENCE_END_RE.findall(stderr)]
    intervals = list(zip(starts, ends))
    return duration, intervals


def _compute_split_points(
    duration: float, silences: list[tuple[float, float]], target_s: float, hard_max_s: float
) -> list[float]:
    midpoints = sorted((start + end) / 2 for start, end in silences)
    splits: list[float] = []
    cursor = 0.0

    while duration - cursor > hard_max_s:
        window_start, window_end = cursor + target_s, cursor + hard_max_s
        candidates = [m for m in midpoints if window_start <= m <= window_end]
        split = min(candidates, key=lambda m: abs(m - window_start)) if candidates else window_end
        splits.append(split)
        cursor = split

    return splits


class ChunkingError(RuntimeError):
    pass


def split_audio(source_path: str, out_dir: Path) -> list[tuple[Path, float]]:
    """Splits on silence into ~chunk_target_minutes pieces (never exceeding
    chunk_max_minutes), re-encoded to mono 16kHz mp3 to keep each chunk small.
    Returns (chunk_path, start_offset_seconds) pairs — the offset is needed to
    shift each chunk's own 0-based Whisper segment timestamps back into
    meeting-global time. Raises ChunkingError if ffmpeg is unavailable or the
    input can't be read.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        duration, silences = _run_silencedetect(source_path)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ChunkingError(f"ffmpeg silence detection failed: {exc}") from exc

    if not duration:
        raise ChunkingError("Could not determine audio duration from ffmpeg output.")

    target_s = settings.chunk_target_minutes * 60
    hard_max_s = settings.chunk_max_minutes * 60
    splits = _compute_split_points(duration, silences, target_s, hard_max_s)
    boundaries = list(zip([0.0, *splits], [*splits, duration]))

    chunks: list[tuple[Path, float]] = []
    for i, (start, end) in enumerate(boundaries):
        chunk_path = out_dir / f"chunk_{i:03d}.mp3"
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error",
                "-i", source_path,
                "-ss", str(start), "-to", str(end),
                "-ar", "16000", "-ac", "1",
                "-c:a", "libmp3lame", "-b:a", "64k",
                str(chunk_path),
            ],
            capture_output=True, text=True, timeout=300, check=False,
        )
        if result.returncode != 0 or not chunk_path.exists():
            raise ChunkingError(f"ffmpeg failed to extract chunk {i}: {result.stderr[-500:]}")
        chunks.append((chunk_path, start))

    return chunks
