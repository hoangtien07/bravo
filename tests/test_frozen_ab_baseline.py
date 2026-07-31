from __future__ import annotations

import hashlib
import json

import pytest

from app.eval.frozen_ab_baseline import FrozenBaselineError, build_baseline, freeze_baseline


def _write(path, value) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _replay() -> dict:
    return {
        "persist_answers": True,
        "runs": [{
            "case_id": "bank.anchor.01",
            "runs": [
                {"mode": "off", "http_status": 200, "answer": "legacy", "grounded": True,
                 "citations": ["source#1"], "latency_ms": 7},
                {"mode": "on", "http_status": 200, "answer": "consultant", "grounded": True,
                 "citations": ["source#1"], "latency_ms": 8},
            ],
        }],
    }


def test_build_and_freeze_baseline_binds_inputs_and_refuses_overwrite(tmp_path):
    fixture = tmp_path / "fixture.yaml"
    fixture.write_text("cases: []\n", encoding="utf-8")
    replay = tmp_path / "replay.json"
    _write(replay, _replay())
    evidence_hash = hashlib.sha256(b"evidence").hexdigest()
    prompt_hash = hashlib.sha256(b"prompt").hexdigest()

    artifact = build_baseline(
        fixture_path=fixture, replay_path=replay, baseline_commit="abc1234",
        model_provider="local", model="test-model", model_version="2026-07-31",
        evidence_snapshot_sha256=evidence_hash, prompt_hashes=[f"legacy={prompt_hash}"],
        captured_at="2026-07-31T00:00:00+00:00",
    )
    path = freeze_baseline(artifact, tmp_path / "frozen")

    assert path.name == "baseline.json"
    assert artifact["cases"][0]["system_a_legacy"]["answer"] == "legacy"
    assert artifact["controls"]["credentials_recorded"] is False
    assert (path.parent / "SHA256SUMS").is_file()
    with pytest.raises(FrozenBaselineError, match="refusing to overwrite"):
        freeze_baseline(artifact, path.parent)


def test_baseline_rejects_missing_matched_answer(tmp_path):
    fixture = tmp_path / "fixture.yaml"
    fixture.write_text("cases: []\n", encoding="utf-8")
    replay = tmp_path / "replay.json"
    incomplete = _replay()
    incomplete["runs"][0]["runs"] = incomplete["runs"][0]["runs"][:1]
    _write(replay, incomplete)
    digest = hashlib.sha256(b"x").hexdigest()

    with pytest.raises(FrozenBaselineError, match="one off and one on"):
        build_baseline(
            fixture_path=fixture, replay_path=replay, baseline_commit="abc1234",
            model_provider="local", model="test-model", model_version="v1",
            evidence_snapshot_sha256=digest, prompt_hashes=[f"legacy={digest}"],
        )
