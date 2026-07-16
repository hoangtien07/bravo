"""Typed, versioned contracts for the consultant layer (Phase 1/2)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RiskClass = Literal["U0", "U1", "U2", "U3", "U4"]
WorkflowEvidenceStatus = Literal["scaffold", "sme_reviewed", "verified"]
ConsultantProfile = Literal["auto", "bravo_user_guide", "implementation", "isms"]


class EnvironmentProfile(BaseModel):
    bravo_version: str | None = None
    module: str | None = None
    customer_environment: str | None = None
    database_schema: str | None = None


class GoalFrame(BaseModel):
    goal_type: str = "unknown"
    confidence: float = 0.0
    profile: ConsultantProfile = "auto"
    environment: EnvironmentProfile = Field(default_factory=EnvironmentProfile)
    constraints: list[str] = Field(default_factory=list)
    risk: RiskClass = "U1"


class TaskState(BaseModel):
    # Incremented on a true goal/workflow switch. Facts are scoped to this task epoch so a
    # technical/configuration request cannot inherit an accounting-close assumption (and vice
    # versa). The bounded history is metadata only; it stores no raw conversation content.
    task_epoch: int = 0
    workflow_id: str | None = None
    superseded_workflow_ids: list[str] = Field(default_factory=list)
    current_node: str | None = None
    completed_nodes: list[str] = Field(default_factory=list)
    facts: dict[str, str | bool | int | float | None] = Field(default_factory=dict)
    open_questions: list[str] = Field(default_factory=list)
    status: Literal["active", "paused", "completed", "cancelled"] = "active"
    revision: int = 0


class RetrievalNeed(BaseModel):
    kind: Literal["business", "bravo_action", "schema", "similar_issue", "policy", "tool"]
    required: bool = False
    query_hint: str = ""


class WorkflowNode(BaseModel):
    id: str
    title: str
    prerequisite_ids: list[str] = Field(default_factory=list)
    retrieval_needs: list[RetrievalNeed] = Field(default_factory=list)
    completion_signals: list[str] = Field(default_factory=list)
    risk: RiskClass = "U1"


class WorkflowCard(BaseModel):
    id: str
    title: str
    goal_type: str
    triggers: list[str] = Field(default_factory=list)
    profile: ConsultantProfile = "auto"
    description: str = ""
    # A workflow can be useful as a business-planning scaffold before exact BRAVO steps are
    # verified. The status is carried to the prompt/trace so that difference remains visible.
    evidence_status: WorkflowEvidenceStatus = "scaffold"
    evidence_refs: list[str] = Field(default_factory=list)
    reviewed_by: str | None = None
    nodes: list[WorkflowNode]


class GoalCard(BaseModel):
    goal_type: str
    title: str
    success_milestones: list[str]
    default_risk: RiskClass = "U1"


class ContextManifest(BaseModel):
    version: str = "consultant-context/v1"
    config_version: str = "consultant/v1"
    goal_type: str
    workflow_id: str | None = None
    workflow_evidence_status: WorkflowEvidenceStatus | None = None
    profile: ConsultantProfile = "auto"
    node_id: str | None = None
    retrieval_needs: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    source_types: list[str] = Field(default_factory=list)
    token_budget: int = 0


class GapEventInput(BaseModel):
    goal_type: str
    workflow_id: str | None = None
    node_id: str | None = None
    reason: Literal["missing_workflow", "missing_evidence", "missing_environment", "missing_schema",
                    "missing_kedb", "provider_unavailable", "wrong_goal", "wrong_step",
                    "unsafe_guidance"]
    risk: RiskClass = "U1"
    signature: str
