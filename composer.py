"""Compose a sentence from word-bank audio clips."""
from pathlib import Path
import io

import database as db


def compose(profile_id: str, sentence: str) -> tuple[bytes | None, list[str]]:
    from pydub import AudioSegment

    words = [w.strip().lower() for w in sentence.split() if w.strip()]
    words = [_clean(w) for w in words]
    words = [w for w in words if w]

    missing = []
    clips = []

    for word in words:
        row = db.get_best_word(profile_id, word)
        if row and Path(row["file_path"]).exists():
            clip = AudioSegment.from_wav(row["file_path"])
            clips.append(clip)
        else:
            missing.append(word)
            clips.append(AudioSegment.silent(duration=300))

    if not clips:
        return None, missing

    silence = AudioSegment.silent(duration=80)
    combined = clips[0]
    for c in clips[1:]:
        combined = combined + silence + c

    buf = io.BytesIO()
    combined.export(buf, format="wav")
    return buf.getvalue(), missing


def _clean(word: str) -> str:
    import re
    return re.sub(r"[^\w]", "", word.lower())
