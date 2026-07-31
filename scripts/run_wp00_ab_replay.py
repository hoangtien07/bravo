"""Run the full synthetic WP-00 A/B replay with an ephemeral synthetic evaluation identity."""
from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import sys
from pathlib import Path

from sqlalchemy import select

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from app.database import async_session_factory
from app.database.models import Employee
from app.eval.consultant_replay import replay
from app.security.passwords import hash_password


async def _identity() -> tuple[str, str]:
    email = "wp00-frozen-ab@invalid.example"
    password = secrets.token_urlsafe(32)
    async with async_session_factory() as db:
        employee = (await db.execute(select(Employee).where(Employee.email == email))).scalar_one_or_none()
        if employee is None:
            employee = Employee(email=email, full_name="WP-00 frozen A/B synthetic evaluator",
                                password_hash=hash_password(password), is_admin=False,
                                permissions=["doc:read:own_dept"])
            db.add(employee)
        else:
            employee.password_hash = hash_password(password)
            employee.permissions = ["doc:read:own_dept"]
        await db.commit()
    return email, password


async def main_async(args: argparse.Namespace) -> dict:
    email, password = await _identity()
    return await replay(args.fixture, base_url=args.base_url, username=email, password=password,
                        max_cases=30, pace_seconds=args.pace_seconds, persist_answers=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", default="app/eval/consultant_benchmark.example.yaml")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--pace-seconds", type=float, default=4.0)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = asyncio.run(main_async(args))
    if report.get("cases") != 30:
        raise SystemExit("WP-00 A/B replay did not complete all 30 synthetic cases")
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WP-00 synthetic A/B replay completed: 30 cases, credentials not persisted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
