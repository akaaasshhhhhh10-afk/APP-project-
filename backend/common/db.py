"""SQLite persistence shared by both services (stands in for the report's Supabase PostgreSQL)."""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import DB_PATH, UPLOAD_DIR

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student','faculty','alumni')),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alumni_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    year INTEGER NOT NULL CHECK (year BETWEEN 1980 AND 2035),
    degree TEXT NOT NULL,
    role TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    skills TEXT NOT NULL DEFAULT '[]',
    bio TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    location TEXT NOT NULL,
    kind TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    poster_path TEXT,
    creator_id TEXT REFERENCES users(id),
    creator_name TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS event_rsvps (
    event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, user_id)
);
CREATE TABLE IF NOT EXISTS mentorship_requests (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alumni_profile_id TEXT NOT NULL REFERENCES alumni_profiles(id) ON DELETE CASCADE,
    message TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','accepted','declined')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    read_at TEXT,
    created_at TEXT NOT NULL
);
"""


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rows(cursor) -> list[dict]:
    return [dict(r) for r in cursor.fetchall()]


def row(cursor) -> dict | None:
    r = cursor.fetchone()
    return dict(r) if r else None


def profile_out(r: dict) -> dict:
    r = dict(r)
    r["skills"] = json.loads(r["skills"])
    return r


def notify(conn: sqlite3.Connection, user_id: str, message: str) -> None:
    conn.execute(
        "INSERT INTO notifications (id, user_id, message, created_at) VALUES (?,?,?,?)",
        (new_id(), user_id, message, now_iso()),
    )


def init_db() -> None:
    from .seed import seed

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        conn.executescript(SCHEMA)
        seed(conn)
