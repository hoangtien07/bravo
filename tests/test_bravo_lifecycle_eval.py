from __future__ import annotations

from types import SimpleNamespace

from app.eval.bravo_lifecycle import BravoLifecycleItem, score_item, summarize


def _chunk(source_id="s1", **extra):
    return SimpleNamespace(source_id=source_id, extra=extra)


def test_bravo_lifecycle_score_hits_source_type_and_module():
    item = BravoLifecycleItem(
        id="bravo-tech-01",
        question="Bang B30BizDoc dung luu gi?",
        actor_email="ketoan@bravo.vn",
        expected_source_types=["technical_manual"],
        expected_modules=["platform"],
        expected_labels=["Technical Manual"],
    )
    res = score_item(
        item,
        [_chunk(source_type="technical_manual", module="platform")],
        source_labels={"s1": "Technical Manual - BRAVO 10 core"},
    )

    assert res.passed
    assert res.top_source_types == ["technical_manual"]
    assert res.top_modules == ["platform"]


def test_bravo_lifecycle_score_fails_wrong_source_type():
    item = BravoLifecycleItem(
        id="bravo-tech-01",
        question="Bang B30BizDoc dung luu gi?",
        actor_email="ketoan@bravo.vn",
        expected_source_types=["technical_manual"],
        expected_modules=["platform"],
    )
    res = score_item(item, [_chunk(source_type="user_guide", module="purchase")])

    assert not res.passed
    assert not res.source_type_hit
    assert not res.module_hit


def test_bravo_lifecycle_summary():
    ok = BravoLifecycleItem("ok", "q", "a", expected_source_types=["user_guide"])
    bad = BravoLifecycleItem("bad", "q", "a", expected_source_types=["technical_manual"])
    results = [
        score_item(ok, [_chunk(source_type="user_guide")]),
        score_item(bad, [_chunk(source_type="mindmap")]),
    ]

    metrics = summarize(results)
    assert metrics["n"] == 2.0
    assert metrics["pass_rate"] == 0.5
