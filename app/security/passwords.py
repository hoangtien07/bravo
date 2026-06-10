"""Password hashing via bcrypt directly (avoids passlib<->bcrypt 4.x incompatibility).

bcrypt truncates at 72 bytes; we truncate explicitly to be safe.
"""
from __future__ import annotations

import bcrypt


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False
