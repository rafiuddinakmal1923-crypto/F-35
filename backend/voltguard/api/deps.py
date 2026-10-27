"""Request dependencies: sign-in token, role checks and the caller's database connection (FR-AD-01)."""

from __future__ import annotations

from typing import Iterator

from fastapi import Depends, Header, HTTPException, status

from voltguard import auth, db
from voltguard.db import Caller


class ApiError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})


def forbidden(message: str = "Your role or region does not allow this") -> ApiError:
    return ApiError(status.HTTP_403_FORBIDDEN, "forbidden", message)


def not_found(what: str = "Not found") -> ApiError:
    return ApiError(status.HTTP_404_NOT_FOUND, "not_found", what)


def bad_request(message: str, code: str = "bad_request") -> ApiError:
    return ApiError(status.HTTP_400_BAD_REQUEST, code, message)


def conflict(message: str) -> ApiError:
    return ApiError(status.HTTP_409_CONFLICT, "conflict", message)


def current_session(authorization: str | None = Header(default=None)) -> auth.Session:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "unauthenticated", "Sign in first")
    try:
        session = auth.decode_token(authorization.split(" ", 1)[1].strip())
    except auth.AuthError as exc:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "unauthenticated", str(exc)) from exc
    # Remote sign-out and deactivation take effect at the next request (NFR-16).
    with db.app_connection(session.caller) as conn:
        row = conn.execute("SELECT token_version, active FROM vg_user_auth(%s)", (session.caller.user_id,)).fetchone()
    if not row or not row["active"] or row["token_version"] != session.token_version:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "signed_out", "This sign-in has been revoked; sign in again")
    return session


def caller(session: auth.Session = Depends(current_session)) -> Caller:
    return session.caller


def require(*roles: str):
    """Dependency: the caller must have one of these roles."""
    def check(c: Caller = Depends(caller)) -> Caller:
        if c.role not in roles:
            raise forbidden(f"This needs one of these roles: {', '.join(roles)}")
        return c
    return check


def connection(c: Caller = Depends(caller)) -> Iterator:
    with db.app_connection(c) as conn:
        yield conn
