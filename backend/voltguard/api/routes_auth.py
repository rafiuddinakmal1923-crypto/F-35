"""Sign-in, current user and remote sign-out (FR-AD-01, NFR-16)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from voltguard import auth, db
from voltguard.api.deps import ApiError, caller, connection, forbidden, not_found, require
from voltguard.db import Caller

router = APIRouter(tags=["auth"])
ANONYMOUS = Caller("anonymous", "anonymous", "")


class SignIn(BaseModel):
    username: str
    password: str


@router.post("/auth/token")
def sign_in(body: SignIn):
    username = body.username.strip().lower()
    if auth.throttled(username):
        raise ApiError(status.HTTP_429_TOO_MANY_REQUESTS, "throttled", "Too many failed attempts; wait five minutes")
    with db.app_connection(ANONYMOUS) as conn:
        user = conn.execute("SELECT * FROM vg_user_auth(%s)", (username,)).fetchone()
        if not user or not user["active"] or not auth.check_password(body.password, user["password_hash"]):
            auth.record_failure(username)
            db.audit(conn, username, "auth.sign_in_failed", None, None)
            raise ApiError(status.HTTP_401_UNAUTHORIZED, "bad_credentials", "Wrong username or password")
        token, expires = auth.issue_token(user)
        db.audit(conn, username, "auth.sign_in", None, {"role": user["role"]})
    return {"access_token": token, "token_type": "bearer", "expires_at": expires,
            "user": {k: user[k] for k in ("user_id", "role", "region", "team")}}


@router.get("/me")
def me(c: Caller = Depends(caller), conn=Depends(connection)):
    row = conn.execute("SELECT user_id, role, region, team, display_name FROM app_user WHERE user_id = %s", (c.user_id,)).fetchone()
    return row or {"user_id": c.user_id, "role": c.role, "region": c.region, "team": c.team}


@router.post("/auth/sign-out")
def sign_out(c: Caller = Depends(caller), conn=Depends(connection)):
    conn.execute("UPDATE app_user SET token_version = token_version + 1 WHERE user_id = %s", (c.user_id,))
    db.audit(conn, c.user_id, "auth.sign_out", f"user:{c.user_id}", None)
    return {"signed_out": True}


@router.get("/users")
def users(c: Caller = Depends(require("supervisor", "admin", "manager")), conn=Depends(connection)):
    return conn.execute("SELECT user_id, role, region, team, display_name, active FROM app_user ORDER BY role, user_id").fetchall()


@router.post("/users/{user_id}/sign-out")
def remote_sign_out(user_id: str, c: Caller = Depends(require("supervisor", "admin")), conn=Depends(connection)):
    """Remote sign-out of a lost phone (NFR-16): every token of that user stops working at once."""
    target = conn.execute("SELECT user_id, role, region FROM app_user WHERE user_id = %s", (user_id,)).fetchone()
    if not target:
        raise not_found("User not found in your region")
    if c.role == "supervisor" and (target["role"] != "inspector" or target["region"] != c.region):
        raise forbidden("Supervisors can sign out inspectors in their region only")
    conn.execute("UPDATE app_user SET token_version = token_version + 1 WHERE user_id = %s", (user_id,))
    db.audit(conn, c.user_id, "auth.remote_sign_out", f"user:{user_id}", None)
    return {"signed_out": user_id}
