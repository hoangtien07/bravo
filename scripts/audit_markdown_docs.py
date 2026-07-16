"""Inventory Markdown documentation without modifying source files.

The report is intentionally evidence-only. Suggested actions are conservative signals for
human review; the script never moves, merges, archives, or deletes documents.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote


IGNORED_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
GENERATED_REPORT = Path("docs/documentation/MARKDOWN-INVENTORY.md")
LINK_RE = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
STATUS_RE = re.compile(
    r"^\s*(?:>\s*)?(?:\*\*)?(?:status|trạng thái|current status|gate status)"
    r"\s*:?\s*(?:\*\*)?\s*:?\s*(.+)",
    re.IGNORECASE,
)
LINK_AUDIT_EXCLUDED_PREFIXES = (
    ".claude/skills/adr-new/",       # deliberate XXXX template links
    "plan-rebuild/bravogen-p0/",     # raw evidence preserves malformed external citations
)


@dataclass
class Document:
    path: Path
    title: str
    status: str
    role: str
    action: str
    reason: str
    tracked: bool
    size: int
    modified: str
    inbound: int = 0
    broken_links: int = 0


def git_lines(root: Path, *args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args], cwd=root, check=False, capture_output=True, text=True
    )
    return {line.replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def markdown_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        base = Path(current)
        for name in files:
            if name.lower().endswith(".md"):
                rel = (base / name).relative_to(root)
                if rel.as_posix() != GENERATED_REPORT.as_posix():
                    found.append(rel)
    return sorted(found, key=lambda item: item.as_posix().lower())


def first_title_and_status(text: str) -> tuple[str, str]:
    title = ""
    status = ""
    for line in text.splitlines()[:30]:
        if not title and line.startswith("# "):
            title = line[2:].strip()
        if not status:
            match = STATUS_RE.search(line.strip(" >*`"))
            if match:
                status = match.group(1).strip(" *`—-")[:120]
    return title, status


def classify(path: Path) -> tuple[str, str, str]:
    posix = path.as_posix()
    lower = posix.lower()
    name = path.name.lower()

    if "/archive/" in f"/{lower}":
        return "archived", "exclude_default", "Archived provenance; never preload as current state"
    if lower.startswith("file_system/"):
        return "domain_data", "exclude_default", "Corpus/data Markdown; not project documentation"
    if lower.startswith("research-paper/"):
        return "external_evidence", "exclude_default", "Research source; open only on demand"
    if "/adr/" in f"/{lower}":
        return "decision", "keep_reference", "ADR history is retained; lifecycle is managed by ADR status"
    if lower.startswith("docs/reviews/"):
        return "review_evidence", "exclude_default", "Historical review/remediation evidence"
    if lower.startswith("docs/research/"):
        return "research_evidence", "exclude_default", "Research evidence, not current project state"
    if lower.startswith("docs/work-packages/"):
        return "implementation_evidence", "exclude_default", "Completed/legacy work-package evidence"
    if lower.startswith("docs/reference/"):
        return "reference", "exclude_default", "Repository/reference notes"
    if lower.startswith("plan-rebuild/bravogen-p0/"):
        return "benchmark_evidence", "exclude_default", "Raw/derived R0 evidence; retain but do not preload"
    if lower.startswith("plan-rebuild/"):
        if name.startswith("deep-research-"):
            return "generated_research_input", "archive_candidate", "Research input/upload derivative"
        return "active_decision", "keep_default", "Current rebuild decision workspace"
    if path.parent == Path(".") or len(path.parts) == 1:
        return "entrypoint", "keep_default", "Repository entrypoint or agent instruction"
    if lower == "docs/consultant-intelligence-implementation.md":
        return "active_implementation", "keep_default", "Current uncommitted implementation status"
    if lower.startswith("docs/") and path.parent == Path("docs"):
        stable = {
            "architecture.md", "vision.md", "security-rls.md", "security-agent-db-role.md",
            "tool-inventory.md", "glossary.md", "bravo-data-runtime-classification.md",
            "corpus-ops.md", "document-management.md", "runbook-dr.md",
            "runbook-packaging.md", "deploy-gcp.md", "secrets.md", "sso-oidc.md",
        }
        if name in stable:
            return "normative_or_runbook", "keep_reference", "Long-lived architecture/security/runbook"
        if any(token in name for token in ("plan", "roadmap", "council", "continuation", "proposal", "agent")):
            return "legacy_plan_or_review", "review_candidate", "Potentially superseded by current rebuild decision"
        return "project_reference", "keep_reference", "Project documentation; verify freshness before preload"
    return "reference", "exclude_default", "Non-canonical Markdown"


def normalize_link(source: Path, raw_target: str, root: Path) -> Path | None:
    target = raw_target.strip().strip("<>").split()[0]
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not target or target.startswith(("#", "http://", "https://", "mailto:", "data:", "app://")):
        return None
    if re.match(r"^/?[A-Za-z]:[/\\]", target):
        return None
    candidate = (root / source.parent / target).resolve()
    try:
        return candidate.relative_to(root.resolve())
    except ValueError:
        return None


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def build_report(root: Path) -> str:
    tracked = git_lines(root, "ls-files", "*.md")
    paths = markdown_files(root)
    path_set = {path.as_posix() for path in paths}
    documents: list[Document] = []
    contents: dict[str, str] = {}
    hashes: defaultdict[str, list[str]] = defaultdict(list)
    inbound: Counter[str] = Counter()
    broken: list[tuple[str, str]] = []

    for path in paths:
        full = root / path
        text = full.read_text(encoding="utf-8", errors="replace")
        contents[path.as_posix()] = text
        hashes[hashlib.sha256(text.encode("utf-8")).hexdigest()].append(path.as_posix())
        title, status = first_title_and_status(text)
        role, action, reason = classify(path)
        stat = full.stat()
        documents.append(Document(
            path=path,
            title=title or "(missing H1)",
            status=status or "(not declared)",
            role=role,
            action=action,
            reason=reason,
            tracked=path.as_posix() in tracked,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).date().isoformat(),
        ))

    for source, text in contents.items():
        if source.startswith(LINK_AUDIT_EXCLUDED_PREFIXES):
            continue
        for match in LINK_RE.finditer(text):
            raw = match.group(1)
            target = normalize_link(Path(source), raw, root)
            if target is None:
                continue
            target_posix = target.as_posix()
            if target_posix in path_set or (root / target).exists():
                inbound[target_posix] += 1
            else:
                broken.append((source, raw))

    broken_count = Counter(source for source, _target in broken)
    for document in documents:
        posix = document.path.as_posix()
        document.inbound = inbound[posix]
        document.broken_links = broken_count[posix]

    duplicate_groups = [items for items in hashes.values() if len(items) > 1]
    action_counts = Counter(document.action for document in documents)
    role_counts = Counter(document.role for document in documents)
    tracked_count = sum(1 for document in documents if document.tracked)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    lines = [
        "# Markdown inventory and cleanup signals",
        "",
        "> Generated by `python scripts/audit_markdown_docs.py`. Do not use this report as",
        "> the current project-state source. Suggested actions are conservative review signals.",
        "",
        f"Generated (UTC): `{generated_at}`  ",
        f"Markdown files inventoried: **{len(documents)}**  ",
        f"Git tracked: **{tracked_count}**; not tracked: **{len(documents) - tracked_count}**  ",
        f"Broken relative-link occurrences: **{len(broken)}**  ",
        f"Exact duplicate groups: **{len(duplicate_groups)}**",
        "",
        "## Suggested-action counts",
        "",
        "| Action | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| `{action}` | {count} |" for action, count in sorted(action_counts.items()))
    lines.extend(["", "## Role counts", "", "| Role | Count |", "|---|---:|"])
    lines.extend(f"| `{role}` | {count} |" for role, count in sorted(role_counts.items()))

    lines.extend(["", "## Exact duplicates", ""])
    if duplicate_groups:
        for group in duplicate_groups:
            lines.append("- " + ", ".join(f"`{item}`" for item in group))
    else:
        lines.append("No exact-content duplicates detected.")

    lines.extend(["", "## Broken relative links", ""])
    if broken:
        lines.extend(f"- `{source}` → `{target}`" for source, target in broken)
    else:
        lines.append("No broken relative links detected.")

    lines.extend([
        "", "## Full inventory", "",
        "| Path | Role | Suggested action | Git | Status marker | Inbound | Broken | Reason |",
        "|---|---|---|---|---|---:|---:|---|",
    ])
    for document in documents:
        lines.append(
            f"| `{document.path.as_posix()}` | `{document.role}` | `{document.action}` | "
            f"{'tracked' if document.tracked else 'untracked'} | {escape_cell(document.status)} | "
            f"{document.inbound} | {document.broken_links} | {escape_cell(document.reason)} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=GENERATED_REPORT)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(root), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
