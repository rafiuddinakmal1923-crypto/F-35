"""Built-in sign-in with the SDD roles, regions and teams (lite profile; Keycloak in the full profile).

Passwords are stored as scrypt hashes. Tokens are signed JWTs carrying the user's role, region,
team and token version; remote sign-out (NFR-16) bumps the version so every older token on a
lost phone stops working at the next request, and the inspector app wipes its local data.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass

import jwt

from voltguard import config
from voltguard.db import Caller

ROLES = ("manager", "analyst", "supervisor", "inspector", "data_scientist", "admin", "auditor", "pipeline")
TOKEN_HOURS = {"inspector": 24}         # phones keep a day's cases at most (NFR-16)
DEFAULT_TOKEN_HOURS = 10
_failures: dict[str, list[float]] = {}  # simple sign-in throttle per user
MAX_FAILURES, WINDOW_S = 5, 300


class AuthError(Exception):
    pass


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def check_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_b64, digest_b64 = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    expected = base64.b64decode(digest_b64)
    actual = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64), n=2**14, r=8, p=1, dklen=32)
    return hmac.compare_digest(expected, actual)


@dataclass(frozen=True)
class Session:
    caller: Caller
    token_version: int
    expires_at: int


def issue_token(user: dict) -> tuple[str, int]:
    hours = TOKEN_HOURS.get(user["role"], DEFAULT_TOKEN_HOURS)
    expires = int(time.time()) + hours * 3600
    payload = {"sub": user["user_id"], "role": user["role"], "region": user["region"], "team": user.get("team"),
               "ver": int(user["token_version"]), "exp": expires, "iat": int(time.time()), "jti": secrets.token_hex(8)}
    return jwt.encode(payload, config.jwt_secret(), algorithm="HS256"), expires


def decode_token(token: str) -> Session:
    try:
        payload = jwt.decode(token, config.jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthError(f"invalid token: {exc}") from exc
    if payload.get("role") not in ROLES:
        raise AuthError("invalid role")
    return Session(Caller(payload["sub"], payload["role"], payload["region"], payload.get("team")), int(payload["ver"]), int(payload["exp"]))


def throttled(user_id: str) -> bool:
    now = time.time()
    recent = [t for t in _failures.get(user_id, []) if now - t < WINDOW_S]
    _failures[user_id] = recent
    return len(recent) >= MAX_FAILURES


def record_failure(user_id: str) -> None:
    _failures.setdefault(user_id, []).append(time.time())


def generate_password() -> str:
    """Strong test-account password (printed by `make.ps1 demo`, stored in .env, never committed)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    return "-".join("".join(secrets.choice(alphabet) for _ in range(5)) for _ in range(4))


def demo_passwords() -> dict[str, str]:
    raw = os.environ.get("DEMO_PASSWORDS", "")
    pairs = (item.split("=", 1) for item in raw.split(",") if "=" in item)
    return {user.strip(): password.strip() for user, password in pairs}
