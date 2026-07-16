"""Stable conversation-level feature assignment for the consultant path (Phase 5)."""
from __future__ import annotations

import hashlib
import uuid


def is_assigned(session_id: uuid.UUID, employee_id: uuid.UUID, percent: int) -> bool:
    """A conversation never flips path mid-thread when percentage changes later."""
    if percent <= 0:
        return False
    if percent >= 100:
        return True
    key = f"{session_id}:{employee_id}".encode()
    bucket = int(hashlib.sha256(key).hexdigest()[:8], 16) % 100
    return bucket < percent
