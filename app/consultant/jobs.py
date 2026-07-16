"""Governed autonomous curation jobs (Phase 4), deliberately provider-neutral."""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ConsultantGapEvent, KnowledgeCandidate


def artifact_type_for_reason(reason: str) -> str:
    """Route a typed gap to a reviewable artifact, never a live knowledge update."""
    return {
        "missing_workflow": "workflow_card",
        "missing_schema": "schema_snapshot_request",
        "missing_kedb": "diagnostic_card",
        "missing_environment": "environment_profile_request",
        "wrong_goal": "workflow_card",
        "unsafe_guidance": "safety_review",
    }.get(reason, "action_map")


async def create_candidates_from_open_gaps(db: AsyncSession, *, limit: int = 100) -> int:
    """Create reviewable artifact briefs. This never publishes raw external output."""
    # The admin endpoint and hourly worker may overlap. Lock only open rows and skip rows another
    # curator owns, so a gap can generate at most one review candidate without serialising the
    # whole queue.
    rows = list((await db.execute(select(ConsultantGapEvent).where(
        ConsultantGapEvent.status == "open").order_by(ConsultantGapEvent.created_at).limit(limit)
        .with_for_update(skip_locked=True))).scalars())
    groups: dict[tuple[str, str | None, str], list[ConsultantGapEvent]] = defaultdict(list)
    for row in rows:
        groups[(row.goal_type, row.workflow_id, row.reason)].append(row)
    created = 0
    for (goal, workflow, reason), events in groups.items():
        candidate = KnowledgeCandidate(
            artifact_type=artifact_type_for_reason(reason),
            status="review_required",
            content={"goal_type": goal, "workflow_id": workflow, "gap_reason": reason,
                     "research_questions": ["What are the prerequisite and exceptions?", "Which BRAVO 10 version/configuration does this apply to?", "What evidence or counterexample would invalidate the step?"]},
            gap_count=len(events),
        )
        db.add(candidate)
        for event in events:
            event.status = "candidate_created"
        created += 1
    await db.commit()
    return created
