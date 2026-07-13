"""Owner-scoped agent output artifacts with explicit provenance."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Artifact
from app.security.rls import Identity


async def create_research_report(db: AsyncSession, *, run_id: uuid.UUID, identity: Identity,
                                 question: str, answer: str, citations: list[str]) -> Artifact:
    artifact = Artifact(
        agent_run_id=run_id,
        owner_id=identity.employee_id,
        kind="research_report",
        title=(question.strip()[:240] or "Báo cáo nghiên cứu") + ".md",
        content=answer,
        provenance={"question": question, "citations": citations, "mode": "deep_research"},
    )
    db.add(artifact)
    await db.commit()
    return artifact


async def get_artifact(db: AsyncSession, artifact_id: uuid.UUID, identity: Identity) -> Artifact | None:
    stmt = select(Artifact).where(Artifact.id == artifact_id)
    if not identity.is_admin:
        stmt = stmt.where(Artifact.owner_id == identity.employee_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_artifacts(db: AsyncSession, identity: Identity, limit: int = 50) -> list[Artifact]:
    stmt = select(Artifact)
    if not identity.is_admin:
        stmt = stmt.where(Artifact.owner_id == identity.employee_id)
    return list((await db.execute(stmt.order_by(Artifact.created_at.desc()).limit(limit))).scalars().all())
