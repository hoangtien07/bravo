"""Redacted capability probe for the synthetic Plan 18 identities."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

from seed_demo import PASSWORD


def identity(email: str) -> dict[str, object]:
    login = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=urllib.parse.urlencode({"username": email, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = json.load(urllib.request.urlopen(login, timeout=10))["access_token"]
    request = urllib.request.Request("http://127.0.0.1:8000/api/me", headers={"Authorization": f"Bearer {token}"})
    value = json.load(urllib.request.urlopen(request, timeout=10))
    return {"is_admin": value["is_admin"], "permissions": sorted(value["permissions"])}


if __name__ == "__main__":
    print(json.dumps({
        "maker": identity("ketoan@bravo.vn"),
        "reviewer": identity("ketoantruong@bravo.vn"),
        "outside_department": identity("kinhdoanh@bravo.vn"),
    }))
