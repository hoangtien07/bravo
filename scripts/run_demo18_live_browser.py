"""Run Plan 18's live Playwright suite without logging or committing credentials.

The password is read from the existing local synthetic seed module and passed only to the spawned
test process.  The Playwright source contains no credential or token literal.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from seed_demo import PASSWORD

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    env = os.environ.copy()
    env.update({
        "DEMO18_MAKER_EMAIL": "ketoan@bravo.vn",
        "DEMO18_REVIEWER_EMAIL": "ketoantruong@bravo.vn",
        "DEMO18_PASSWORD": PASSWORD,
    })
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/run-playwright.ps1", "e2e/live-demo.pw.ts"],
        cwd=ROOT / "FigmaMake_UI", env=env, check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
