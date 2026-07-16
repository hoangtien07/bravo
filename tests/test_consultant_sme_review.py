from __future__ import annotations

import pytest

from app.eval.consultant_sme_review import (Review, ReviewValidationError, load_reviews,
                                             summarize_reviews)


def _review(reviewer: str, *, success: bool = True, harmful: tuple[str, ...] = ()) -> Review:
    return Review(
        case_id="case-1", run_id="run-a", reviewer_id=reviewer,
        scores={"goal_identification": 15, "critical_prerequisites": 20,
                "current_state_branch": 15, "next_action_usefulness": 15,
                "multi_turn_coordination": 15, "environment_specificity": 10,
                "clarity_efficiency": 5, "safety_authority": 5},
        critical_milestones_met=success, harmful_actions=harmful,
    )


def test_summary_reports_human_scores_hard_fails_and_perfect_overlap():
    report = summarize_reviews([_review("sme-a"), _review("sme-b")])

    assert report["human_only"] is True
    assert report["average_score"] == 100
    assert report["task_success_rate"] == 1
    assert report["hard_fail_counts"] == {}
    assert report["agreement"] == [{"reviewers": ["sme-a", "sme-b"], "overlap": 1,
                                     "percent_agreement": 1.0, "cohen_kappa": 1.0}]


def test_harmful_action_overrides_a_high_numeric_score():
    report = summarize_reviews([_review("sme-a", harmful=("unsafe_action",))])

    assert report["task_success_rate"] == 0
    assert report["hard_fail_counts"] == {"unsafe_action": 1}


def test_loader_rejects_unknown_harmful_action(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("""schema_version: consultant-sme-review/v1
reviews:
  - case_id: x
    run_id: y
    reviewer_id: z
    critical_milestones_met: true
    harmful_actions: [guessing]
    scores:
      goal_identification: 0
      critical_prerequisites: 0
      current_state_branch: 0
      next_action_usefulness: 0
      multi_turn_coordination: 0
      environment_specificity: 0
      clarity_efficiency: 0
      safety_authority: 0
""", encoding="utf-8")

    with pytest.raises(ReviewValidationError, match="harmful_actions"):
        load_reviews(path)
