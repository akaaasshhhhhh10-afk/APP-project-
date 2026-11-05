"""Flask service (port 5000): Authentication, Faculty Directory Governance and Mentorship workflow.

Routes: /api/auth/*, /api/alumni/*, /api/mentorship/*
"""
import json
import sqlite3
import sys
from functools import wraps
from pathlib import Path

import jwt
from flask import Flask, g, jsonify, request
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.config import CORS_ORIGINS  # noqa: E402
from common.db import db, init_db, new_id, notify, now_iso, profile_out, row, rows  # noqa: E402
from common.security import decode_token, hash_password, issue_session, public_user, verify_password  # noqa: E402

app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)

ROLES = {"student", "faculty", "alumni"}


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        self.message, self.status = message, status


@app.errorhandler(ApiError)
def handle_api_error(err: ApiError):
    return jsonify({"detail": err.message}), err.status


def require_auth(*roles):
    """Validates the Bearer token and loads the user into flask.g; optionally restricts by role."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                raise ApiError("Missing bearer token", 401)
            try:
                payload = decode_token(header[7:])
            except jwt.PyJWTError:
                raise ApiError("Invalid or expired token", 401)
            with db() as conn:
                user = row(conn.execute("SELECT * FROM users WHERE id = ?", (payload["sub"],)))
            if not user:
                raise ApiError("Account no longer exists", 401)
            if roles and user["role"] not in roles:
                raise ApiError("You do not have permission for this action", 403)
            g.user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Expected a JSON object body")
    return data


def clean_name(name: str, email: str) -> str:
    """Report 3.2: derive a display name from the email prefix when omitted."""
    import re

    raw = (name or "").strip() or email.split("@")[0]
    return re.sub(r"\b\w", lambda m: m.group().upper(), re.sub(r"[._]", " ", raw))


# ---------------------------------------------------------------- authentication


@app.post("/api/auth/signup")
def signup():
    data = body()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    role = str(data.get("role", "student")).lower()
    if "@" not in email:
        raise ApiError("Enter a valid email address")
    if len(password) < 8:
        raise ApiError("Password must be at least 8 characters")
    if role not in ROLES:
        raise ApiError("Role must be student, faculty or alumni")
    user = {"id": new_id(), "name": clean_name(data.get("name", ""), email), "email": email, "role": role}
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO users (id, name, email, password_hash, role, created_at) VALUES (?,?,?,?,?,?)",
                (user["id"], user["name"], email, hash_password(password), role, now_iso()),
            )
    except sqlite3.IntegrityError:
        raise ApiError("An account with this email already exists", 409)
    return jsonify(issue_session(user)), 201


@app.post("/api/auth/login")
def login():
    data = body()
    email = str(data.get("email", "")).strip().lower()
    with db() as conn:
        user = row(conn.execute("SELECT * FROM users WHERE email = ?", (email,)))
    if not user or not verify_password(str(data.get("password", "")), user["password_hash"]):
        raise ApiError("Incorrect email or password", 401)
    return jsonify(issue_session(user))


@app.post("/api/auth/refresh")
def refresh():
    try:
        payload = decode_token(str(body().get("refresh_token", "")), kind="refresh")
    except jwt.PyJWTError:
        raise ApiError("Invalid or expired refresh token", 401)
    with db() as conn:
        user = row(conn.execute("SELECT * FROM users WHERE id = ?", (payload["sub"],)))
    if not user:
        raise ApiError("Account no longer exists", 401)
    return jsonify(issue_session(user))


@app.get("/api/auth/me")
@require_auth()
def me():
    return jsonify(public_user(g.user))


@app.post("/api/auth/logout")
@require_auth()
def logout():
    # Tokens are stateless; the client discards them. Endpoint exists so the UI has a single sign-out call.
    return jsonify({"ok": True})


# ---------------------------------------------------------------- alumni directory


def read_profile_fields(data: dict) -> dict:
    """Validates and normalises a directory record (report 3.2: skill tokenising, year bounds)."""
    out = {}
    for field in ("name", "degree", "role", "company", "location"):
        value = str(data.get(field, "")).strip()
        if not value:
            raise ApiError(f"{field.capitalize()} is required")
        out[field] = value
    try:
        out["year"] = int(data.get("year"))
    except (TypeError, ValueError):
        raise ApiError("Graduation year must be a number")
    if not 1980 <= out["year"] <= 2035:
        raise ApiError("Graduation year must be between 1980 and 2035")
    skills = data.get("skills", [])
    if isinstance(skills, str):
        skills = skills.split(",")
    out["skills"] = json.dumps([s.strip() for s in skills if str(s).strip()])
    out["bio"] = str(data.get("bio", "")).strip()
    return out


@app.get("/api/alumni")
@require_auth()
def list_alumni():
    with db() as conn:
        data = rows(conn.execute("SELECT * FROM alumni_profiles ORDER BY year DESC, name"))
    return jsonify([profile_out(p) for p in data])


@app.post("/api/alumni")
@require_auth("faculty", "alumni")
def create_alumnus():
    fields = read_profile_fields(body())
    pid = new_id()
    with db() as conn:
        user_id = None
        if g.user["role"] == "alumni":  # alumni may only create the one profile that belongs to them
            if row(conn.execute("SELECT id FROM alumni_profiles WHERE user_id = ?", (g.user["id"],))):
                raise ApiError("You already have a profile; edit it instead", 409)
            user_id = g.user["id"]
        conn.execute(
            "INSERT INTO alumni_profiles (id, user_id, name, year, degree, role, company, location, skills, bio)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (pid, user_id, fields["name"], fields["year"], fields["degree"], fields["role"],
             fields["company"], fields["location"], fields["skills"], fields["bio"]),
        )
        created = row(conn.execute("SELECT * FROM alumni_profiles WHERE id = ?", (pid,)))
    return jsonify(profile_out(created)), 201


@app.patch("/api/alumni/<pid>")
@require_auth("faculty", "alumni")
def update_alumnus(pid):
    with db() as conn:
        current = row(conn.execute("SELECT * FROM alumni_profiles WHERE id = ?", (pid,)))
        if not current:
            raise ApiError("Alumnus not found", 404)
        if g.user["role"] == "alumni" and current["user_id"] != g.user["id"]:
            raise ApiError("You can only edit your own profile", 403)
        merged = {**profile_out(current), **body()}
        f = read_profile_fields(merged)
        conn.execute(
            "UPDATE alumni_profiles SET name=?, year=?, degree=?, role=?, company=?, location=?, skills=?, bio=?"
            " WHERE id=?",
            (f["name"], f["year"], f["degree"], f["role"], f["company"], f["location"], f["skills"], f["bio"], pid),
        )
        updated = row(conn.execute("SELECT * FROM alumni_profiles WHERE id = ?", (pid,)))
    return jsonify(profile_out(updated))


@app.delete("/api/alumni/<pid>")
@require_auth("faculty")
def delete_alumnus(pid):
    with db() as conn:
        if conn.execute("DELETE FROM alumni_profiles WHERE id = ?", (pid,)).rowcount == 0:
            raise ApiError("Alumnus not found", 404)
    return "", 204


# ---------------------------------------------------------------- mentorship workflow

MENTORSHIP_SELECT = """
SELECT m.id, m.student_id, m.alumni_profile_id, m.message, m.status, m.created_at, m.updated_at,
       s.name AS student_name, a.name AS alumni_name, a.company AS alumni_company, a.user_id AS alumni_user_id
FROM mentorship_requests m
JOIN users s ON s.id = m.student_id
JOIN alumni_profiles a ON a.id = m.alumni_profile_id
"""


@app.get("/api/mentorship")
@require_auth()
def list_requests():
    user = g.user
    with db() as conn:
        if user["role"] == "student":
            cur = conn.execute(MENTORSHIP_SELECT + " WHERE m.student_id = ? ORDER BY m.created_at DESC", (user["id"],))
        elif user["role"] == "alumni":
            cur = conn.execute(MENTORSHIP_SELECT + " WHERE a.user_id = ? ORDER BY m.created_at DESC", (user["id"],))
        else:
            cur = conn.execute(MENTORSHIP_SELECT + " ORDER BY m.created_at DESC")
        return jsonify(rows(cur))


@app.post("/api/mentorship")
@require_auth("student")
def create_request():
    data = body()
    pid = str(data.get("alumni_profile_id", ""))
    message = str(data.get("message", "")).strip()[:500]
    with db() as conn:
        alumnus = row(conn.execute("SELECT * FROM alumni_profiles WHERE id = ?", (pid,)))
        if not alumnus:
            raise ApiError("Alumnus not found", 404)
        active = conn.execute(
            "SELECT 1 FROM mentorship_requests WHERE student_id = ? AND alumni_profile_id = ? AND status != 'declined'",
            (g.user["id"], pid),
        ).fetchone()
        if active:
            raise ApiError("You already have an active request with this alumnus", 409)
        rid, ts = new_id(), now_iso()
        conn.execute(
            "INSERT INTO mentorship_requests (id, student_id, alumni_profile_id, message, status, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (rid, g.user["id"], pid, message, "pending", ts, ts),
        )
        if alumnus["user_id"]:
            notify(conn, alumnus["user_id"], f"{g.user['name']} requested mentorship from you.")
        notify(conn, g.user["id"], f"Mentorship request sent to {alumnus['name']}.")
        created = row(conn.execute(MENTORSHIP_SELECT + " WHERE m.id = ?", (rid,)))
    return jsonify(created), 201


@app.patch("/api/mentorship/<rid>")
@require_auth("alumni")
def resolve_request(rid):
    status = str(body().get("status", "")).lower()
    if status not in {"accepted", "declined"}:
        raise ApiError("Status must be accepted or declined")
    with db() as conn:
        req = row(conn.execute(MENTORSHIP_SELECT + " WHERE m.id = ?", (rid,)))
        if not req:
            raise ApiError("Request not found", 404)
        if req["alumni_user_id"] != g.user["id"]:
            raise ApiError("This request is not addressed to you", 403)
        if req["status"] != "pending":
            raise ApiError(f"Request was already {req['status']}", 409)
        conn.execute("UPDATE mentorship_requests SET status = ?, updated_at = ? WHERE id = ?", (status, now_iso(), rid))
        notify(conn, req["student_id"], f"{req['alumni_name']} {status} your mentorship request.")
        updated = row(conn.execute(MENTORSHIP_SELECT + " WHERE m.id = ?", (rid,)))
    return jsonify(updated)


@app.get("/api/health")
def health():
    return jsonify({"service": "flask", "ok": True})


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
