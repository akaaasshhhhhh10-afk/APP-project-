"""Password hashing and JWT helpers shared by the Flask and FastAPI services."""
import hashlib
import hmac
import os
import time

import jwt

from .config import ACCESS_TTL_SECONDS, JWT_SECRET, REFRESH_TTL_SECONDS

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), _ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def _encode(user: dict, kind: str, ttl: int) -> str:
    now = int(time.time())
    payload = {"sub": user["id"], "role": user["role"], "typ": kind, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def issue_session(user: dict) -> dict:
    now = int(time.time())
    return {
        "access_token": _encode(user, "access", ACCESS_TTL_SECONDS),
        "refresh_token": _encode(user, "refresh", REFRESH_TTL_SECONDS),
        "expires_at": now + ACCESS_TTL_SECONDS,
        "user": public_user(user),
    }


def decode_token(token: str, kind: str = "access") -> dict:
    """Raises jwt.PyJWTError on any invalid, expired or wrong-type token."""
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    if payload.get("typ") != kind:
        raise jwt.InvalidTokenError("wrong token type")
    return payload


def public_user(user: dict) -> dict:
    return {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
