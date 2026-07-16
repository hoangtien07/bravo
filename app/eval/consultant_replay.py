"""Run a privacy-safe legacy-versus-consultant replay over the local chat API.

The runner evaluates observable behavior and keeps no bearer token or raw response artifact by
default. It is intentionally not an automatic SME judge: output contains latency, terminal state,
and typed workflow state only. Use the resulting task ids for blind SME review.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from pathlib import Path
from time import perf_counter
from typing import Any

from app.utils.yaml_compat import safe_load_file


async def _post_turn(client: Any, base_url: str, headers: dict[str, str], question: str,
                     consultant_mode: str) -> dict[str, Any]:
    conversation_id = str(uuid.uuid4())
    started = perf_counter()
    response = await client.post(
        f"{base_url}/api/chat/{conversation_id}/messages", headers=headers,
        json={"question": question, "consultant_mode": consultant_mode}, timeout=90,
    )
    elapsed_ms = round((perf_counter() - started) * 1000)
    state = await client.get(f"{base_url}/api/consultant/state/{conversation_id}", headers=headers)
    state_json = state.json() if state.status_code == 200 else {}
    return {"conversation_id": conversation_id, "mode": consultant_mode,
            "http_status": response.status_code, "latency_ms": elapsed_ms,
            "workflow_id": state_json.get("workflow_id"),
            "current_node": state_json.get("current_node"),
            "state_revision": state_json.get("revision")}


async def replay(fixture: str | Path, *, base_url: str, username: str, password: str,
                 max_cases: int | None = None, pace_seconds: float = 2.0) -> dict[str, Any]:
    try:
        import httpx
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("Install project dependencies before replay.") from exc
    raw = safe_load_file(Path(fixture)) or {}
    cases = list(raw.get("cases", []))[:max_cases]
    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        login = await client.post(f"{base_url}/api/auth/login", data={"username": username, "password": password})
        login.raise_for_status()
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        for case in cases:
            # First turn only: it gives a controlled A/B question without inventing a user action.
            turns = case.get("turns") or []
            if not turns:
                continue
            question = str(turns[0]["user"])
            pair = await asyncio.gather(
                _post_turn(client, base_url, headers, question, "off"),
                _post_turn(client, base_url, headers, question, "on"),
            )
            results.append({"case_id": case.get("case_id"), "runs": pair})
            # Two turns use the same demo identity. Pace below the default per-user rate limit
            # instead of treating rate-limit errors as model behavior.
            if pace_seconds > 0:
                await asyncio.sleep(pace_seconds)
    return {"fixture": str(fixture), "cases": len(results), "runs": results,
            "note": "No answer text, credential, or customer data is persisted by this runner."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", default="app/eval/consultant_benchmark.example.yaml")
    parser.add_argument("--base-url", default=os.getenv("BRAVO_LOCAL_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--username", default=os.getenv("BRAVO_EVAL_USERNAME", ""))
    parser.add_argument("--password", default=os.getenv("BRAVO_EVAL_PASSWORD", ""))
    parser.add_argument("--max-cases", type=int)
    parser.add_argument("--pace-seconds", type=float, default=2.0)
    parser.add_argument("--out")
    args = parser.parse_args()
    if not args.username or not args.password:
        raise SystemExit("Set BRAVO_EVAL_USERNAME and BRAVO_EVAL_PASSWORD; credentials are never stored.")
    report = asyncio.run(replay(args.fixture, base_url=args.base_url, username=args.username,
                                password=args.password, max_cases=args.max_cases,
                                pace_seconds=args.pace_seconds))
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
