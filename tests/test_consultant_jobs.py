from sqlalchemy.dialects import postgresql

from app.consultant.jobs import artifact_type_for_reason
from app.database.models import ConsultantGapEvent
from sqlalchemy import select


def test_candidate_artifact_mapping_covers_typed_gaps():
    assert artifact_type_for_reason("missing_workflow") == "workflow_card"
    assert artifact_type_for_reason("missing_schema") == "schema_snapshot_request"
    assert artifact_type_for_reason("missing_kedb") == "diagnostic_card"


def test_open_gap_claim_uses_skip_locked_for_concurrent_curators():
    statement = (select(ConsultantGapEvent).where(ConsultantGapEvent.status == "open")
                 .order_by(ConsultantGapEvent.created_at).limit(100).with_for_update(skip_locked=True))

    compiled = str(statement.compile(dialect=postgresql.dialect()))

    assert "FOR UPDATE SKIP LOCKED" in compiled
