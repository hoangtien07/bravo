"""Non-secret local Knowledge Chat SSE smoke for Plan 18.

It emits only aggregate event metadata; no token, password or answer content is printed.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
import uuid

from seed_demo import PASSWORD


def main() -> None:
    login = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=urllib.parse.urlencode({"username": "ketoan@bravo.vn", "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = json.load(urllib.request.urlopen(login, timeout=10))["access_token"]
    request = urllib.request.Request(
        f"http://127.0.0.1:8000/api/chat/{uuid.uuid4()}/messages",
        data=json.dumps({
            "question": "Hãy xác nhận bạn có thể trả lời từ tri thức BRAVO.",
            "attachment_ids": [], "source_ids": [], "mode": "auto", "web_access": "off",
            "consultant_mode": "auto", "consultant_profile": "auto",
        }).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "text/event-stream"},
    )
    raw = urllib.request.urlopen(request, timeout=60).read().decode(errors="replace")
    print(json.dumps({
        "terminal_done": '"type": "done"' in raw,
        "error_events": raw.count('"type": "error"'),
        "source_events": raw.count('"type": "source"'),
        "answer_events": raw.count('"type": "answer"'),
    }))


if __name__ == "__main__":
    main()
