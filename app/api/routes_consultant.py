"""Read-only visibility and governed curation controls for Consultant Intelligence."""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.consultant.catalog import load_catalog
from app.consultant.evidence import (lookup_schema, schema_fingerprint, search_kedb,
                                     validate_schema_payload)
from app.consultant.jobs import create_candidates_from_open_gaps
from app.consultant.service import ConsultantService
from app.database import get_db
from app.database.models import (AuditLog, ConsultantGapEvent, Conversation, KnownError,
                                 KnowledgeCandidate, SchemaSnapshot)
from app.security.auth import get_current_identity, require_admin, require_permission
from app.security.rls import Identity

router = APIRouter(prefix="/consultant")


class CandidateReviewIn(BaseModel):
    decision: str  # approve | reject; approval still does not activate knowledge
    note: str = ""


class ConsultantFeedbackIn(BaseModel):
    kind: Literal["wrong_goal", "wrong_step", "unsafe_guidance"]


class SchemaSnapshotIn(BaseModel):
    bravo_version: str
    environment: str
    source_ref: str = ""
    payload: dict


class EvidenceReviewIn(BaseModel):
    decision: str  # verify | reject | deprecate


class KnownErrorIn(BaseModel):
    case_key: str
    title: str
    symptom: str
    probable_cause: str | None = None
    resolution: str | None = None
    bravo_version: str | None = None
    environment: str | None = None
    source_refs: list[str] = []


class KnownErrorReviewIn(BaseModel):
    decision: str  # verify | reject | supersede
    supersedes_case_key: str | None = None


@router.get("/status")
async def status(identity: Identity = Depends(get_current_identity),
                 db: AsyncSession = Depends(get_db)) -> dict:
    """Return only caller-owned state; no transcript or raw external data."""
    return {"enabled": get_settings().consultant_enabled,
            "rollout_percent": get_settings().consultant_rollout_percent,
            "external_expert_enabled": False,
            "curation": {"enabled": get_settings().consultant_curation_enabled,
                         "cadence": "hourly", "promotion": "review_required_only"},
            "task_state_retention": {
                "enabled": get_settings().consultant_state_retention_enabled,
                "cadence": "daily",
                "scope": "consultant_task_state_only",
                "policy_duration_configured": bool(get_settings().consultant_state_retention_days),
            },
            "catalog_version": "v1",
            "profiles": [
                {"id": "auto", "available": True},
                {"id": "bravo_user_guide", "available": True},
                {"id": "implementation", "available": True},
                {"id": "isms", "available": False,
                 "reason": "No approved ISMS/policy corpus is available."},
            ],
            "state_endpoint": "/api/consultant/state/{conversation_id}"}


@router.get("/state/{conversation_id}")
async def conversation_state(conversation_id: uuid.UUID,
                             identity: Identity = Depends(get_current_identity),
                             db: AsyncSession = Depends(get_db)) -> dict:
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None or (conversation.employee_id != identity.employee_id and not identity.is_admin):
        raise HTTPException(status_code=404, detail="Conversation not found")
    state = await ConsultantService(db, identity, conversation_id).load_state()
    payload = state.model_dump(mode="json")
    workflow = load_catalog()[1].get(state.workflow_id) if state.workflow_id else None
    # This is catalog metadata only; it exposes neither the transcript nor source content.
    payload["workflow_evidence_status"] = workflow.evidence_status if workflow else None
    return payload


@router.post("/state/{conversation_id}/feedback")
async def state_feedback(conversation_id: uuid.UUID, body: ConsultantFeedbackIn,
                         identity: Identity = Depends(get_current_identity),
                         db: AsyncSession = Depends(get_db)) -> dict:
    """Capture a typed dogfood signal without retaining answer text or a raw transcript copy."""
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None or (conversation.employee_id != identity.employee_id and not identity.is_admin):
        raise HTTPException(status_code=404, detail="Conversation not found")
    created = await ConsultantService(db, identity, conversation_id).record_structured_feedback(body.kind)
    return {"created": created, "kind": body.kind, "promotion": "review_required_only"}


@router.get("/gaps")
async def gaps(identity: Identity = Depends(require_admin),
               db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = (await db.execute(select(ConsultantGapEvent.goal_type, ConsultantGapEvent.workflow_id,
                                    ConsultantGapEvent.reason, ConsultantGapEvent.risk,
                                    func.count(ConsultantGapEvent.id).label("count"))
                             .group_by(ConsultantGapEvent.goal_type, ConsultantGapEvent.workflow_id,
                                       ConsultantGapEvent.reason, ConsultantGapEvent.risk)
                             .order_by(func.count(ConsultantGapEvent.id).desc()))).all()
    return [{"goal_type": row.goal_type, "workflow_id": row.workflow_id,
             "reason": row.reason, "risk": row.risk, "count": row.count} for row in rows]


@router.post("/jobs/curate")
async def curate(identity: Identity = Depends(require_admin),
                 db: AsyncSession = Depends(get_db)) -> dict:
    """Creates review-required briefs; it never queries a provider or activates knowledge."""
    created = await create_candidates_from_open_gaps(db)
    return {"created": created, "status": "review_required"}


@router.get("/candidates")
async def candidates(identity: Identity = Depends(require_admin),
                     db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = list((await db.execute(select(KnowledgeCandidate).order_by(
        KnowledgeCandidate.created_at.desc()).limit(100))).scalars())
    return [{"id": str(row.id), "artifact_type": row.artifact_type, "status": row.status,
             "gap_count": row.gap_count, "content": row.content, "review_note": row.review_note,
             "created_at": row.created_at}
            for row in rows]


@router.post("/candidates/{candidate_id}/review")
async def review_candidate(candidate_id: uuid.UUID, body: CandidateReviewIn,
                           identity: Identity = Depends(require_admin),
                           db: AsyncSession = Depends(get_db)) -> dict:
    if body.decision not in {"approve", "reject"}:
        raise HTTPException(status_code=422, detail="decision must be approve or reject")
    target = "approved_candidate" if body.decision == "approve" else "rejected"
    reviewed = (await db.execute(
        update(KnowledgeCandidate)
        .where(KnowledgeCandidate.id == candidate_id,
               KnowledgeCandidate.status == "review_required")
        .values(status=target, reviewer_id=identity.employee_id,
                review_note=body.note.strip()[:2000] or None)
        .returning(KnowledgeCandidate.id, KnowledgeCandidate.status)
    )).one_or_none()
    if reviewed is None:
        exists = await db.get(KnowledgeCandidate, candidate_id)
        if exists is None:
            raise HTTPException(status_code=404, detail="Candidate not found")
        raise HTTPException(status_code=409, detail="Candidate was already reviewed")
    db.add(AuditLog(actor_id=identity.employee_id, action="consultant.candidate.review",
                    detail={"candidate_id": str(candidate_id), "from": "review_required",
                            "to": target, "decision": body.decision}))
    await db.commit()
    # Promotion to active cards/index is intentionally a separate, evidence-gated operation.
    return {"id": str(reviewed.id), "status": reviewed.status, "active": False}


# --- Schema grounding: metadata snapshots only; no live database access. ----------------------
@router.post("/schema-snapshots")
async def create_schema_snapshot(body: SchemaSnapshotIn,
                                 identity: Identity = Depends(require_admin),
                                 db: AsyncSession = Depends(get_db)) -> dict:
    payload = validate_schema_payload(body.payload)
    fingerprint = schema_fingerprint({"version": body.bravo_version, "environment": body.environment,
                                      "payload": payload})
    existing = (await db.execute(select(SchemaSnapshot).where(
        SchemaSnapshot.fingerprint == fingerprint))).scalar_one_or_none()
    if existing:
        return {"id": str(existing.id), "status": existing.status, "duplicate": True}
    row = SchemaSnapshot(bravo_version=body.bravo_version.strip()[:80],
                         environment=body.environment.strip()[:120], status="candidate",
                         source_ref=body.source_ref.strip()[:500] or None, fingerprint=fingerprint,
                         payload=payload, created_by=identity.employee_id)
    db.add(row)
    await db.commit()
    return {"id": str(row.id), "status": row.status, "duplicate": False}


@router.post("/schema-snapshots/{snapshot_id}/review")
async def review_schema_snapshot(snapshot_id: uuid.UUID, body: EvidenceReviewIn,
                                 identity: Identity = Depends(require_admin),
                                 db: AsyncSession = Depends(get_db)) -> dict:
    if body.decision not in {"verify", "reject", "deprecate"}:
        raise HTTPException(status_code=422, detail="decision must be verify, reject, or deprecate")
    target = {"verify": "verified", "reject": "rejected", "deprecate": "deprecated"}[body.decision]
    expected = "verified" if body.decision == "deprecate" else "candidate"
    values = {"status": target}
    if body.decision == "verify":
        values["approved_by"] = identity.employee_id
    reviewed = (await db.execute(
        update(SchemaSnapshot)
        .where(SchemaSnapshot.id == snapshot_id, SchemaSnapshot.status == expected)
        .values(**values)
        .returning(SchemaSnapshot.id, SchemaSnapshot.status)
    )).one_or_none()
    if reviewed is None:
        exists = await db.get(SchemaSnapshot, snapshot_id)
        if exists is None:
            raise HTTPException(status_code=404, detail="Schema snapshot not found")
        raise HTTPException(status_code=409, detail=f"Schema snapshot must be {expected}")
    db.add(AuditLog(actor_id=identity.employee_id, action="consultant.schema.review",
                    detail={"snapshot_id": str(snapshot_id), "from": expected,
                            "to": target, "decision": body.decision}))
    await db.commit()
    return {"id": str(reviewed.id), "status": reviewed.status}


@router.get("/schema-lookup")
async def schema_lookup(query: str, bravo_version: str | None = None, environment: str | None = None,
                        identity: Identity = Depends(require_permission("doc:read")),
                        db: AsyncSession = Depends(get_db)) -> dict:
    facts = await lookup_schema(db, query, bravo_version=bravo_version, environment=environment)
    return {"facts": facts, "verified_only": True,
            "message": None if facts else "No verified schema snapshot matched this version/environment."}


# --- KEDB: a resolution can be retrieved only after an explicit verification decision. ----------
@router.post("/kedb")
async def create_known_error(body: KnownErrorIn, identity: Identity = Depends(require_admin),
                             db: AsyncSession = Depends(get_db)) -> dict:
    key = body.case_key.strip()[:120]
    if not key:
        raise HTTPException(status_code=422, detail="case_key is required")
    existing = (await db.execute(select(KnownError).where(KnownError.case_key == key))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="case_key already exists")
    row = KnownError(case_key=key, title=body.title.strip()[:500], symptom=body.symptom.strip(),
                     probable_cause=body.probable_cause, resolution=body.resolution,
                     bravo_version=body.bravo_version, environment=body.environment,
                     source_refs=[ref[:500] for ref in body.source_refs[:20]], status="candidate",
                     created_by=identity.employee_id)
    db.add(row)
    await db.commit()
    return {"id": str(row.id), "status": row.status}


@router.post("/kedb/{entry_id}/review")
async def review_known_error(entry_id: uuid.UUID, body: KnownErrorReviewIn,
                             identity: Identity = Depends(require_admin),
                             db: AsyncSession = Depends(get_db)) -> dict:
    if body.decision not in {"verify", "reject", "supersede"}:
        raise HTTPException(status_code=422, detail="decision must be verify, reject, or supersede")
    if body.decision == "supersede" and not body.supersedes_case_key:
        raise HTTPException(status_code=422, detail="supersedes_case_key is required to supersede")
    target = {"verify": "verified", "reject": "rejected", "supersede": "superseded"}[body.decision]
    expected = "verified" if body.decision == "supersede" else "candidate"
    values = {"status": target}
    if body.decision == "supersede":
        values["supersedes_case_key"] = body.supersedes_case_key
    if body.decision == "verify":
        values["verified_by"] = identity.employee_id
    reviewed = (await db.execute(
        update(KnownError)
        .where(KnownError.id == entry_id, KnownError.status == expected)
        .values(**values)
        .returning(KnownError.id, KnownError.status)
    )).one_or_none()
    if reviewed is None:
        exists = await db.get(KnownError, entry_id)
        if exists is None:
            raise HTTPException(status_code=404, detail="KEDB entry not found")
        raise HTTPException(status_code=409, detail=f"KEDB entry must be {expected}")
    db.add(AuditLog(actor_id=identity.employee_id, action="consultant.kedb.review",
                    detail={"entry_id": str(entry_id), "from": expected,
                            "to": target, "decision": body.decision}))
    await db.commit()
    return {"id": str(reviewed.id), "status": reviewed.status}


@router.get("/kedb/search")
async def kedb_search(query: str, bravo_version: str | None = None, environment: str | None = None,
                      identity: Identity = Depends(require_permission("doc:read")),
                      db: AsyncSession = Depends(get_db)) -> list[dict]:
    rows = await search_kedb(db, query, bravo_version=bravo_version, environment=environment)
    return [{"id": str(row.id), "case_key": row.case_key, "title": row.title,
             "symptom": row.symptom, "probable_cause": row.probable_cause,
             "resolution": row.resolution, "bravo_version": row.bravo_version,
             "environment": row.environment, "source_refs": row.source_refs,
             "status": row.status} for row in rows]
