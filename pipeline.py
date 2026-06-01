"""
Download -> convert -> transcribe -> slice pipeline.
"""
import re
import shutil
import threading
from pathlib import Path

import database as db
from paths import data_dir, ensure_ffmpeg_on_path, whisper_model_dir

ensure_ffmpeg_on_path()

DATA_DIR = data_dir() / "profiles"


def profile_dir(profile_id: str) -> Path:
    p = DATA_DIR / profile_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def words_dir(profile_id: str) -> Path:
    p = profile_dir(profile_id) / "words"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _sanitize(word: str) -> str:
    return re.sub(r"[^\w]", "", word.lower())


def _download_audio(url: str, out_path: Path, progress_cb) -> Path:
    import yt_dlp

    progress_cb("Mengunduh audio dari YouTube...", 5)
    mp3_path = out_path.with_suffix(".mp3")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(out_path.with_suffix("")),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "unknown")
    progress_cb(f"Download selesai: {title}", 20)
    return mp3_path


def _copy_local_audio(src: str, out_path: Path, progress_cb) -> Path:
    import shutil as sh
    progress_cb("Menyalin file audio...", 5)
    dest = out_path.with_suffix(Path(src).suffix)
    sh.copy2(src, dest)
    progress_cb("File disalin.", 10)
    return dest


def _convert_to_wav(audio_path: Path, progress_cb) -> Path:
    from pydub import AudioSegment
    progress_cb("Konversi ke WAV...", 25)
    wav_path = audio_path.with_suffix(".wav")
    audio = AudioSegment.from_file(str(audio_path))
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(str(wav_path), format="wav")
    progress_cb("Konversi selesai.", 30)
    return wav_path


def _trim_wav(wav_path: Path, start_sec: float | None, end_sec: float | None, progress_cb) -> Path:
    if start_sec is None and end_sec is None:
        return wav_path
    from pydub import AudioSegment
    audio = AudioSegment.from_wav(str(wav_path))
    duration_sec = len(audio) / 1000
    start_ms = int((start_sec or 0) * 1000)
    end_ms = int((end_sec or duration_sec) * 1000)
    end_ms = min(end_ms, len(audio))
    trimmed = audio[start_ms:end_ms]
    trimmed.export(str(wav_path), format="wav")
    return wav_path


def _transcribe(wav_path: Path, progress_cb) -> list:
    from faster_whisper import WhisperModel
    bundled = whisper_model_dir()
    model_ref = str(bundled) if bundled else "base"
    model = WhisperModel(model_ref, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(wav_path), word_timestamps=True, language=None)
    words = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                clean = _sanitize(w.word)
                if clean:
                    words.append({"word": clean, "start": w.start, "end": w.end, "prob": w.probability})
    return words


def _slice_words(wav_path: Path, words: list, profile_id: str, progress_cb) -> list[dict]:
    from pydub import AudioSegment
    audio = AudioSegment.from_wav(str(wav_path))
    wdir = words_dir(profile_id)
    instance_count: dict[str, int] = {}
    entries = []
    for i, w in enumerate(words):
        word = w["word"]
        idx = instance_count.get(word, 0)
        instance_count[word] = idx + 1
        start_ms = max(0, int(w["start"] * 1000) - 30)
        end_ms = int(w["end"] * 1000) + 30
        clip = audio[start_ms:end_ms]
        fpath = wdir / f"{word}_{idx}.wav"
        clip.export(str(fpath), format="wav")
        entries.append({
            "word": word,
            "file_path": str(fpath),
            "start_time": w["start"],
            "end_time": w["end"],
            "confidence": w["prob"],
            "instance_index": idx,
        })
    return entries


def run_pipeline(profile_id: str, source: str, is_url: bool, progress_cb, done_cb, start_sec: float | None = None, end_sec: float | None = None):
    def _work():
        try:
            pdir = profile_dir(profile_id)
            raw_out = pdir / "source_raw"
            if is_url:
                audio_path = _download_audio(source, raw_out, progress_cb)
                db.update_profile(profile_id, source_url=source)
            else:
                audio_path = _copy_local_audio(source, raw_out, progress_cb)
                db.update_profile(profile_id, source_file=source)
            wav_path = _convert_to_wav(audio_path, progress_cb)
            wav_path = _trim_wav(wav_path, start_sec, end_sec, progress_cb)
            words = _transcribe(wav_path, progress_cb)
            if not words:
                done_cb(False, "Tidak ada kata yang terdeteksi dalam audio.")
                return
            db.clear_words(profile_id)
            old_wdir = words_dir(profile_id)
            if old_wdir.exists():
                shutil.rmtree(old_wdir)
            entries = _slice_words(wav_path, words, profile_id, progress_cb)
            db.insert_words(profile_id, entries)
            done_cb(True, f"Berhasil! {len(set(e['word'] for e in entries))} kata unik tersimpan di word bank.")
        except Exception as e:
            done_cb(False, f"Error: {e}")
    threading.Thread(target=_work, daemon=True).start()
