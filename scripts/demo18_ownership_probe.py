"""Redacted local ownership proof for Plan 18 conversation, attachment and source routes."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid

from seed_demo import PASSWORD

BASE = "http://127.0.0.1:8000/api"


def login(email: str) -> str:
    request = urllib.request.Request(f"{BASE}/auth/login", data=urllib.parse.urlencode({"username": email, "password": PASSWORD}).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
    return json.load(urllib.request.urlopen(request, timeout=15))["access_token"]


def json_request(path: str, token: str, body: dict | None = None, method: str | None = None) -> dict:
    request = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode() if body is not None else None, method=method, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def status(path: str, token: str, *, method: str = "GET") -> int:
    request = urllib.request.Request(f"{BASE}{path}", method=method, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def multipart(path: str, token: str, filename: str) -> dict:
    boundary = "----demo18" + uuid.uuid4().hex
    body = b"\r\n".join((
        f"--{boundary}".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode(),
        b"Content-Type: text/plain", b"",
        b"Synthetic Plan 18 ownership probe. No customer or ERP data.",
        f"--{boundary}--".encode(), b"",
    ))
    request = urllib.request.Request(f"{BASE}{path}", data=body, headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def conversation(maker: str) -> str:
    conversation_id = str(uuid.uuid4())
    request = urllib.request.Request(f"{BASE}/chat/{conversation_id}/messages", data=json.dumps({"question": "Plan 18 ownership probe", "web_access": "off"}).encode(), headers={"Authorization": f"Bearer {maker}", "Content-Type": "application/json", "Accept": "text/event-stream"})
    terminal = False
    with urllib.request.urlopen(request, timeout=90) as response:
        for line in response:
            if line.startswith(b"data:"):
                try:
                    terminal = terminal or json.loads(line[5:]).get("type") == "done"
                except json.JSONDecodeError:
                    pass
    if not terminal:
        raise RuntimeError("conversation did not reach terminal done")
    return conversation_id


if __name__ == "__main__":
    maker = login("ketoan@bravo.vn")
    outside = login("kinhdoanh@bravo.vn")
    conversation_id = conversation(maker)
    attachment = multipart("/attachments", maker, "demo18-ownership-attachment.txt")
    source = multipart("/sources", maker, "demo18-ownership-source.txt")
    try:
        outside_sources = json_request("/sources", outside)
        print(json.dumps({
            "non_owner_conversation_404": status(f"/conversations/{conversation_id}", outside) == 404,
            "non_owner_attachment_404": status(f"/attachments/{attachment['id']}", outside) == 404,
            "personal_source_absent_from_outside_list": all(row.get("id") != source["id"] for row in outside_sources),
        }, sort_keys=True))
    finally:
        # These objects were created by this probe under the maker identity only.
        status(f"/conversations/{conversation_id}", maker, method="DELETE")
        status(f"/attachments/{attachment['id']}", maker, method="DELETE")
        status(f"/sources/{source['id']}", maker, method="DELETE")
