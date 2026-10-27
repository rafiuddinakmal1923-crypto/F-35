"""Encrypted file storage for inspection photos and exported PDFs (lite profile for MinIO).

Files live under DATA_ROOT/photos and DATA_ROOT/pdfs, encrypted with Fernet (AES-128-CBC +
HMAC). Keys are random object names; only the case service hands them out, after its role and
case checks, so a file is never reachable by path guessing or from outside the API.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets

from cryptography.fernet import Fernet

from voltguard import config

BUCKETS = ("photos", "pdfs")
MAX_BYTES = 15 * 1024 * 1024


def _fernet() -> Fernet:
    key = os.environ.get("FILE_KEY")
    if not key:
        # Derived from the JWT secret so a fresh setup needs no extra secret; set FILE_KEY to rotate separately.
        key = base64.urlsafe_b64encode(hashlib.sha256(("files:" + config.jwt_secret()).encode()).digest()).decode()
    return Fernet(key)


def _path(bucket: str, key: str):
    if bucket not in BUCKETS or not key.replace("-", "").replace(".", "").isalnum():
        raise ValueError("bad storage key")
    return config.data_path(bucket, key)


def put(bucket: str, data: bytes, suffix: str = "") -> str:
    if len(data) > MAX_BYTES:
        raise ValueError("file too large")
    key = secrets.token_hex(16) + suffix
    _path(bucket, key).write_bytes(_fernet().encrypt(data))
    return key


def get(bucket: str, key: str) -> bytes:
    return _fernet().decrypt(_path(bucket, key).read_bytes())


def exists(bucket: str, key: str) -> bool:
    try:
        return _path(bucket, key).exists()
    except ValueError:
        return False
