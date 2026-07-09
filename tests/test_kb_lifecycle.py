"""KB version/lifecycle retrieval policy (Findings O #5, VersionRAG mitigation)."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.rag.kb_lifecycle import apply_version_policy, version_weight


@dataclass
class _R:
    chunk_id: str
    score: float
    extra: dict = field(default_factory=dict)


def test_weight_by_status():
    assert version_weight({"approved_status": "approved"}) == 0.0
    assert version_weight({}) == 0.0
    assert version_weight({"approved_status": "superseded"}) > 0
    assert version_weight({"approved_status": "deprecated"}) > 0
    assert version_weight({"approved_status": "SUPERSEDED"}) > 0  # case-insensitive
    # superseded_by implies superseded even without explicit status
    assert version_weight({"superseded_by": "coa_tt99_v2026"}) > 0
    # draft demoted less than superseded
    assert 0 < version_weight({"approved_status": "draft"}) < version_weight(
        {"approved_status": "superseded"})


def test_superseded_sinks_below_current_even_if_more_similar():
    # Stale chunk has the HIGHER raw score but must end up below the approved one.
    results = [
        _R("old", 0.90, {"approved_status": "superseded"}),
        _R("new", 0.70, {"approved_status": "approved"}),
    ]
    ordered = apply_version_policy(results)
    assert [r.chunk_id for r in ordered] == ["new", "old"]


def test_noop_when_all_approved():
    results = [_R("a", 0.9, {"approved_status": "approved"}), _R("b", 0.8, {})]
    before = [(r.chunk_id, r.score) for r in results]
    ordered = apply_version_policy(results)
    assert [(r.chunk_id, r.score) for r in ordered] == before  # unchanged order + scores


def test_empty_is_safe():
    assert apply_version_policy([]) == []


def test_deprecated_still_retrievable_when_only_option():
    # Not a hard filter: a lone deprecated chunk is still returned (better than nothing).
    results = [_R("only", 0.5, {"approved_status": "deprecated"})]
    ordered = apply_version_policy(results)
    assert [r.chunk_id for r in ordered] == ["only"]
