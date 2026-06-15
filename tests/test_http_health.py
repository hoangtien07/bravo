"""HTTP integration (TestClient) — lấp gap deep-dive 'không có HTTP-level test'.

Kiểm app boot được + middleware + health endpoints. /livez không cần DB nên chạy mọi nơi.
"""
from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient
    _HAVE_TESTCLIENT = True
except Exception:  # pragma: no cover
    _HAVE_TESTCLIENT = False

pytestmark = pytest.mark.skipif(not _HAVE_TESTCLIENT, reason="TestClient (httpx) chưa cài")


def test_livez_and_request_id_header():
    from app.main import app

    with TestClient(app) as client:
        r = client.get("/livez")
        assert r.status_code == 200 and r.json()["status"] == "alive"
        assert r.headers.get("X-Request-ID")          # middleware gắn request-id


def test_readyz_reports_catalog_loaded():
    from app.main import app

    with TestClient(app) as client:
        r = client.get("/readyz")
        body = r.json()
        # catalog phải đã nạp (>0) — DB có thể ok (200) hoặc không reachable (503) tuỳ môi trường
        assert body["checks"]["catalog"] >= 19
        assert r.status_code in (200, 503)


def test_unauthenticated_protected_route_rejected():
    from app.main import app

    with TestClient(app) as client:
        r = client.post("/api/invoices/draft")  # thiếu auth + file
        assert r.status_code in (401, 422)       # 401 chưa auth / 422 thiếu field
