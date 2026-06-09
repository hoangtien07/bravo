"""Read-only ERP REST client (Phase 2). Reads ONLY approved views/metrics; passes
scope (department/unit/period) down so RLS holds end-to-end. Never writes.
"""
from __future__ import annotations

# TODO(Phase 2): httpx client to BRAVO ERP REST API (read-only).
# Depends on BRAVO confirming the ERP read API surface (VISION §8 open question).
raise_on_import = False
