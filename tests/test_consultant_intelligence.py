import pytest

from app.consultant.catalog import load_catalog, match_workflow
from app.consultant.contracts import TaskState
from app.consultant.service import ConsultantService, _risk
from app.consultant.rollout import is_assigned
from app.consultant.critic import review
from app.consultant.service import PreparedConsultantTurn
from app.consultant.contracts import ContextManifest, GoalFrame
from app.eval.consultant_benchmark import evaluate_fixture, fixture_coverage
from app.consultant.jobs import artifact_type_for_reason


def _service():
    return object.__new__(ConsultantService)


def test_catalog_has_ten_valid_workflows():
    goals, workflows = load_catalog()
    assert len(goals) == 10
    assert len(workflows) == 10


def test_catalog_refuses_unproven_verified_workflow(tmp_path):
    catalog = tmp_path / "catalog.yaml"
    catalog.write_text("""goals:
  - goal_type: test
    title: Test
    success_milestones: [done]
workflows:
  - id: test
    title: Test
    goal_type: test
    evidence_status: verified
    nodes: [{id: done, title: Done}]
""", encoding="utf-8")
    with pytest.raises(ValueError, match="evidence_refs"):
        load_catalog(str(catalog))


def test_gap_artifact_type_matches_evidence_needed():
    assert artifact_type_for_reason("missing_schema") == "schema_snapshot_request"
    assert artifact_type_for_reason("missing_kedb") == "diagnostic_card"
    assert artifact_type_for_reason("missing_workflow") == "workflow_card"
    assert artifact_type_for_reason("missing_evidence") == "action_map"
    assert artifact_type_for_reason("wrong_goal") == "workflow_card"
    assert artifact_type_for_reason("unsafe_guidance") == "safety_review"


def test_financial_close_tracks_prerequisites_and_correction():
    service = _service()
    workflow = match_workflow("Làm sao lên báo cáo tài chính?")
    state = service._reconcile(TaskState(), "Làm sao lên báo cáo tài chính?", workflow)
    assert state.current_node == "scope_known"
    state = service._reconcile(state, "Đã hạch toán, đã đối chiếu, tháng 5 năm 2026 nhưng chưa kết chuyển.", workflow)
    assert state.facts["period"] == "2026-05"
    assert state.facts["posting_checked"] is True
    assert state.facts["reconciliation_checked"] is True
    assert state.current_node == "closing_complete"


def test_correction_rewinds_fact_and_keeps_known_year_for_month_only():
    service = _service()
    workflow = match_workflow("BCTC")
    state = service._reconcile(TaskState(), "Đã hạch toán, đã đối chiếu, tháng 5 năm 2026", workflow)
    assert state.current_node == "closing_complete"

    corrected = service._reconcile(state, "Không, chưa đối chiếu; làm kỳ tháng 6", workflow)

    assert corrected.facts["reconciliation_checked"] is False
    assert corrected.facts["period"] == "2026-06"
    assert corrected.current_node == "reconciliation_checked"


def test_workflow_switch_starts_new_task_epoch_without_old_facts():
    service = _service()
    close = match_workflow("BCTC")
    technical = match_workflow("Layout XML")
    old = service._reconcile(TaskState(), "Đã hạch toán tháng 5 năm 2026", close)

    switched = service._reconcile(old, "Chuyển sang Layout XML", technical)

    assert switched.task_epoch == 1
    assert switched.superseded_workflow_ids == ["financial_close"]
    assert switched.workflow_id == "technical_configuration"
    assert "posting_checked" not in switched.facts
    assert switched.status == "active"


def test_version_correction_and_normal_usage_do_not_pause_task():
    service = _service()
    workflow = match_workflow("BCTC")

    state = service._reconcile(
        TaskState(), "Đang dùng BRAVO 10.2 chứ không phải BRAVO 10.1 để khóa sổ", workflow)

    assert state.facts["bravo_version"] == "10.2"
    assert state.status == "active"


def test_risky_requests_are_draft_only_class():
    assert _risk("Hãy chạy script sửa database") == "U4"
    assert _risk("Viết Layout XML") == "U3"


def test_example_trajectory_fixture_replays():
    results = evaluate_fixture("app/eval/consultant_benchmark.example.yaml")
    assert all(result.passed for result in results), [r.failures for r in results]


def test_fixture_meets_phase_zero_structural_coverage_floor():
    coverage = fixture_coverage("app/eval/consultant_benchmark.example.yaml")
    assert coverage["scenarios"] >= 30
    assert coverage["structural_variants"] >= 100


def test_rollout_is_stable_per_conversation():
    import uuid
    session, employee = uuid.uuid4(), uuid.uuid4()
    assert is_assigned(session, employee, 100)
    assert not is_assigned(session, employee, 0)
    assert is_assigned(session, employee, 37) == is_assigned(session, employee, 37)


def test_critic_prevents_jump_to_financial_report_before_close():
    workflow = match_workflow("BCTC")
    turn = PreparedConsultantTurn(
        frame=GoalFrame(goal_type="financial_statements_ready"),
        state=TaskState(workflow_id="financial_close", current_node="posting_checked"),
        workflow=workflow,
        manifest=ContextManifest(goal_type="financial_statements_ready"),
        prompt_block="",
    )
    result = review("Bạn mở báo cáo tài chính để in.", turn)
    assert "prerequisite_guard" in result.tags
    assert "khóa sổ" in result.answer
