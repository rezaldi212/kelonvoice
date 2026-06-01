"""
Path helpers that behave correctly both in dev and when frozen with PyInstaller.
"""
import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def app_root() -> Path:
    if is_frozen():
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def resource_root() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    p = app_root() / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


def vendor_dir() -> Path:
    candidates = [app_root() / "vendor", resource_root() / "vendor"]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def ffmpeg_dir() -> Path | None:
    p = vendor_dir() / "ffmpeg"
    return p if p.exists() else None


def whisper_model_dir() -> Path | None:
    p = vendor_dir() / "whisper-base"
    return p if p.exists() else None


def ensure_ffmpeg_on_path() -> None:
    d = ffmpeg_dir()
    if d is None:
        return
    current = os.environ.get("PATH", "")
    if str(d) not in current.split(os.pathsep):
        os.environ["PATH"] = str(d) + os.pathsep + current
