import sqlite3
import uuid
from datetime import datetime

from paths import data_dir

DB_PATH = data_dir() / "kelonvoice.db"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                source_url  TEXT,
                source_file TEXT,
                created_at  TEXT NOT NULL,
                word_count  INTEGER DEFAULT 0,
                thumb_path  TEXT
            );

            CREATE TABLE IF NOT EXISTS words (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id     TEXT NOT NULL,
                word           TEXT NOT NULL,
                file_path      TEXT NOT NULL,
                start_time     REAL,
                end_time       REAL,
                confidence     REAL,
                instance_index INTEGER DEFAULT 0,
                FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_words_lookup
                ON words(profile_id, word);
        """)


def create_profile(name: str, source_url: str = None) -> str:
    pid = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO profiles (id, name, source_url, created_at) VALUES (?,?,?,?)",
            (pid, name, source_url, datetime.now().isoformat()),
        )
    return pid


def get_all_profiles() -> list:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM profiles ORDER BY created_at DESC"
        ).fetchall()]


def get_profile(profile_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM profiles WHERE id=?", (profile_id,)
        ).fetchone()
        return dict(row) if row else None


def update_profile(profile_id: str, **kwargs):
    allowed = {"name", "source_url", "source_file", "word_count", "thumb_path"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    with get_conn() as conn:
        conn.execute(
            f"UPDATE profiles SET {sets} WHERE id=?",
            (*fields.values(), profile_id),
        )


def delete_profile(profile_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM profiles WHERE id=?", (profile_id,))


def insert_words(profile_id: str, entries: list[dict]):
    with get_conn() as conn:
        conn.executemany(
            """INSERT INTO words
               (profile_id, word, file_path, start_time, end_time, confidence, instance_index)
               VALUES (:profile_id, :word, :file_path, :start_time, :end_time,
                       :confidence, :instance_index)""",
            [{**e, "profile_id": profile_id} for e in entries],
        )
        conn.execute(
            "UPDATE profiles SET word_count = (SELECT COUNT(DISTINCT word) FROM words WHERE profile_id=?) WHERE id=?",
            (profile_id, profile_id),
        )


def get_words_for_profile(profile_id: str, search: str = "") -> list[dict]:
    with get_conn() as conn:
        if search:
            rows = conn.execute(
                "SELECT * FROM words WHERE profile_id=? AND word LIKE ? ORDER BY word, instance_index",
                (profile_id, f"%{search}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM words WHERE profile_id=? ORDER BY word, instance_index",
                (profile_id,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_best_word(profile_id: str, word: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT * FROM words
               WHERE profile_id=? AND word=?
               ORDER BY confidence DESC LIMIT 1""",
            (profile_id, word.lower()),
        ).fetchone()
        return dict(row) if row else None


def get_unique_words(profile_id: str) -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT word FROM words WHERE profile_id=? ORDER BY word",
            (profile_id,),
        ).fetchall()
        return [r["word"] for r in rows]


def clear_words(profile_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM words WHERE profile_id=?", (profile_id,))
        conn.execute("UPDATE profiles SET word_count=0 WHERE id=?", (profile_id,))
