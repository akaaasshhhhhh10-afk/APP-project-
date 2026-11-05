"""FastAPI service (port 8000): Community Events + poster storage, Notification Center, Search and Stats.

Routes: /api/events/*, /api/notifications/*, /api/search, /api/stats, /uploads/*
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.config import ALLOWED_POSTER_TYPES, CORS_ORIGINS, MAX_POSTER_BYTES, UPLOAD_DIR  # noqa: E402
from common.db import db, init_db, new_id, notify, now_iso, profile_out, row, rows  # noqa: E402
from common.security import decode_token  # noqa: E402

try:
    init_db()
except sqlite3.IntegrityError:  # the Flask service seeded the database at the same moment
    pass

app = FastAPI(title="Alumni Connect - Events & Insights API")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

EVENT_KINDS = {"Community", "Workshop", "Talk", "Networking", "Reunion"}


def current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    try:
        payload = decode_token(authorization[7:])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    with db() as conn:
        user = row(conn.execute("SELECT * FROM users WHERE id = ?", (payload["sub"],)))
    if not user:
        raise HTTPException(401, "Account no longer exists")
    return user


User = Annotated[dict, Depends(current_user)]


# ---------------------------------------------------------------- events


def event_out(event: dict) -> dict:
    event = dict(event)
    path = event.pop("poster_path")
    event["poster_url"] = f"/uploads/{path}" if path else None
    event["going"] = bool(event["going"])
    return event


EVENT_QUERY = """
SELECT e.*, (SELECT COUNT(*) FROM event_rsvps r WHERE r.event_id = e.id) AS rsvp_count,
       EXISTS(SELECT 1 FROM event_rsvps r WHERE r.event_id = e.id AND r.user_id = ?) AS going
FROM events e
"""


@app.get("/api/events")
def list_events(user: User, upcoming: bool = True):
    """Report Algorithm 2 step 2: keep events whose end is in the future, ordered by start time."""
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    sql = EVENT_QUERY + (" WHERE e.ends_at > ?" if upcoming else " WHERE ? IS NOT NULL") + " ORDER BY e.starts_at"
    with db() as conn:
        data = rows(conn.execute(sql, (user["id"], now)))
    return [event_out(e) for e in data]


@app.post("/api/events", status_code=201)
async def create_event(
    user: User,
    title: Annotated[str, Form()],
    starts_at: Annotated[str, Form()],
    ends_at: Annotated[str, Form()],
    location: Annotated[str, Form()],
    kind: Annotated[str, Form()] = "Community",
    description: Annotated[str, Form()] = "",
    poster: UploadFile | None = File(None),
):
    title, location, description = title.strip(), location.strip(), description.strip()
    if not title or len(title) > 80:
        raise HTTPException(422, "Title is required and must be 80 characters or fewer")
    if not location:
        raise HTTPException(422, "Location is required")
    if len(description) > 500:
        raise HTTPException(422, "Description must be 500 characters or fewer")
    if kind not in EVENT_KINDS:
        raise HTTPException(422, f"Kind must be one of {sorted(EVENT_KINDS)}")
    try:
        start, end = datetime.fromisoformat(starts_at), datetime.fromisoformat(ends_at)
    except ValueError:
        raise HTTPException(422, "Dates must be ISO formatted")
    if end <= start:
        raise HTTPException(422, "The end time must be after the start time.")

    poster_path = None
    if poster and poster.filename:
        ext = ALLOWED_POSTER_TYPES.get(poster.content_type)
        if not ext:
            raise HTTPException(422, "Poster must be a JPEG, PNG or WebP image")
        content = await poster.read(MAX_POSTER_BYTES + 1)
        if len(content) > MAX_POSTER_BYTES:
            raise HTTPException(413, "Poster must be 1.5 MB or smaller")
        poster_path = f"{user['id']}-{new_id()}{ext}"  # server-generated name: no client path ever touches disk
        (UPLOAD_DIR / poster_path).write_bytes(content)

    eid = new_id()
    with db() as conn:
        conn.execute(
            "INSERT INTO events (id, title, starts_at, ends_at, location, kind, description, poster_path, creator_id, creator_name)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (eid, title, start.strftime("%Y-%m-%dT%H:%M"), end.strftime("%Y-%m-%dT%H:%M"), location, kind,
             description, poster_path, user["id"], user["name"]),
        )
        for other in conn.execute("SELECT id FROM users WHERE id != ?", (user["id"],)).fetchall():
            notify(conn, other["id"], f"New event: {title}")
        created = row(conn.execute(EVENT_QUERY + " WHERE e.id = ?", (user["id"], eid)))
    return event_out(created)


@app.post("/api/events/{event_id}/rsvp")
def toggle_rsvp(event_id: str, user: User):
    with db() as conn:
        if not conn.execute("SELECT 1 FROM events WHERE id = ?", (event_id,)).fetchone():
            raise HTTPException(404, "Event not found")
        removed = conn.execute(
            "DELETE FROM event_rsvps WHERE event_id = ? AND user_id = ?", (event_id, user["id"])
        ).rowcount
        if not removed:
            conn.execute("INSERT INTO event_rsvps (event_id, user_id) VALUES (?,?)", (event_id, user["id"]))
        count = conn.execute("SELECT COUNT(*) FROM event_rsvps WHERE event_id = ?", (event_id,)).fetchone()[0]
    return {"going": not removed, "rsvp_count": count}


@app.delete("/api/events/{event_id}", status_code=204)
def delete_event(event_id: str, user: User):
    with db() as conn:
        event = row(conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)))
        if not event:
            raise HTTPException(404, "Event not found")
        if user["role"] != "faculty" and event["creator_id"] != user["id"]:
            raise HTTPException(403, "Only the creator or faculty can delete this event")
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    if event["poster_path"]:
        (UPLOAD_DIR / event["poster_path"]).unlink(missing_ok=True)


# ---------------------------------------------------------------- notifications


@app.get("/api/notifications")
def list_notifications(user: User):
    with db() as conn:
        data = rows(conn.execute(
            "SELECT id, message, read_at, created_at FROM notifications WHERE user_id = ? ORDER BY created_at DESC, rowid DESC",
            (user["id"],),
        ))
    return [{**n, "read": n["read_at"] is not None} for n in data]


@app.post("/api/notifications/read-all")
def mark_all_read(user: User):
    with db() as conn:
        conn.execute("UPDATE notifications SET read_at = ? WHERE user_id = ? AND read_at IS NULL", (now_iso(), user["id"]))
    return {"ok": True}


@app.post("/api/notifications/{notification_id}/read")
def mark_read(notification_id: str, user: User):
    with db() as conn:
        updated = conn.execute(
            "UPDATE notifications SET read_at = COALESCE(read_at, ?) WHERE id = ? AND user_id = ?",
            (now_iso(), notification_id, user["id"]),
        ).rowcount
    if not updated:
        raise HTTPException(404, "Notification not found")
    return {"ok": True}


# ---------------------------------------------------------------- search & stats


@app.get("/api/search")
def search_alumni(user: User, q: str = "", limit: int = 100):
    """Server-side version of the report's composite-vector search: every term must match name/role/company/skills/degree."""
    terms = q.lower().split()
    with db() as conn:
        data = [profile_out(p) for p in rows(conn.execute("SELECT * FROM alumni_profiles ORDER BY year DESC, name"))]

    def vector(p: dict) -> str:
        return f"{p['name']} {p['role']} {p['company']} {' '.join(p['skills'])} {p['degree']}".lower()

    return [p for p in data if all(t in vector(p) for t in terms)][: max(1, min(limit, 500))]


@app.get("/api/stats")
def stats(user: User):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM alumni_profiles").fetchone()[0]
        companies = conn.execute("SELECT COUNT(DISTINCT company) FROM alumni_profiles").fetchone()[0]
        upcoming = conn.execute("SELECT COUNT(*) FROM events WHERE ends_at > ?", (now,)).fetchone()[0]
        by_status = {r["status"]: r["n"] for r in conn.execute(
            "SELECT status, COUNT(*) AS n FROM mentorship_requests GROUP BY status")}
        by_year = {str(r["year"]): r["n"] for r in conn.execute(
            "SELECT year, COUNT(*) AS n FROM alumni_profiles GROUP BY year ORDER BY year")}
        by_city = [dict(r) for r in conn.execute(
            "SELECT location, COUNT(*) AS n FROM alumni_profiles GROUP BY location ORDER BY n DESC LIMIT 5")]
    return {
        "alumni": total, "companies": companies, "upcoming_events": upcoming,
        "requests": {s: by_status.get(s, 0) for s in ("pending", "accepted", "declined")},
        "alumni_by_year": by_year, "top_locations": by_city,
    }


@app.get("/api/health")
def health():
    return {"service": "fastapi", "ok": True}
