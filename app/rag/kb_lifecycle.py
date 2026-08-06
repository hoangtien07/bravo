"""KB version/lifecycle policy for retrieval (VersionRAG mitigation, Findings O #5).

Naive RAG answers version-sensitive questions from whichever chunk is most similar —
which is often a STALE/superseded document (wrong-but-sourced). This module applies a
small, deterministic policy AFTER retrieval/rerank: chunks whose source is marked
superseded/deprecated/draft in `Chunk.extra` are demoted so the current version wins
when both are retrieved.

Metadata (knowledge-as-data, set in `file_system/bravo_corpus_manifest.yaml`):
  approved_status : approved | draft | superseded | deprecated   (default: approved)
  superseded_by   : id/version of the doc that replaces this one  (implies superseded)
  effective_date  : ISO date the content became effective         (informational)

This is NOT a hard filter — a demoted chunk still ranks above nothing, so retrieval never
starves. It only reorders. Engine owns the policy; data owns the status.
"""
from __future__ import annotations

from dataclasses import dataclass

# Demotion weights, expressed as a fraction of the result set's top score so the penalty
# scales with whatever stage produced the scores (RRF ~0.03, rerank ~0.1, boost ~0.05).
_STATUS_WEIGHT: dict[str, float] = {
    "superseded": 0.50,
    "deprecated": 0.50,
    "draft": 0.15,
}


@dataclass(frozen=True)
class ExactClaimRequirement:
    """Authority required before an answer may state an exact BRAVO fact.

    Lifecycle demotion is deliberately insufficient here: an exact deployed-version
    claim must have a matching approved source, not merely a highly ranked one.
    """

    doc_version: str
    customer_scope: str = "global"
    effective_on_required: bool = False


def exact_claim_matches(extra: dict | None, requirement: ExactClaimRequirement) -> bool:
    """Return true only for an approved source with matching version/scope authority."""
    extra = extra or {}
    if str(extra.get("approved_status") or "").strip().lower() != "approved":
        return False
    if str(extra.get("doc_version") or "").strip().upper() != requirement.doc_version.strip().upper():
        return False
    source_scope = str(extra.get("customer_scope") or "").strip()
    if source_scope not in {"global", requirement.customer_scope}:
        return False
    if requirement.effective_on_required and not extra.get("effective_date"):
        return False
    return True


def exact_claim_evidence(results: list, requirement: ExactClaimRequirement) -> list:
    """Fail closed by removing sources that cannot support an exact claim."""
    return [result for result in results if exact_claim_matches(getattr(result, "extra", None), requirement)]


def version_weight(extra: dict | None) -> float:
    """Return the demotion weight for a chunk based on its lifecycle metadata."""
    extra = extra or {}
    status = str(extra.get("approved_status") or "").strip().lower()
    if not status and extra.get("superseded_by"):
        status = "superseded"
    return _STATUS_WEIGHT.get(status, 0.0)


def apply_version_policy(results: list) -> list:
    """Demote superseded/deprecated/draft chunks in-place and return re-sorted results.

    No-op when every chunk is `approved` (or carries no lifecycle metadata) — so it is
    safe to call unconditionally in the retrieval pipeline.
    """
    if not results:
        return results
    hi = max((float(getattr(r, "score", 0.0)) for r in results), default=0.0) or 1.0
    changed = False
    for r in results:
        w = version_weight(getattr(r, "extra", None))
        if w:
            r.score = float(getattr(r, "score", 0.0)) - w * hi
            changed = True
    if not changed:
        return results
    return sorted(results, key=lambda r: r.score, reverse=True)
