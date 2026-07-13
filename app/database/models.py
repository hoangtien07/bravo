"""SQLAlchemy ORM models.

Design follows SECURITY-RLS.md: resources are scoped to departments; a resource
with ZERO departments is GLOBAL (visible to all with read permission). RLS is
enforced in SQL (app/security/rls.py), never in app memory.

Provenance fields on Chunk implement the zero-hallucination requirement (VISION §4.1):
every chunk traces back to page/sheet/cell so citations are verifiable. (This is the
gap docsgpt left — we add it.)
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.database import Base

_DIM = get_settings().embedding_dim

# P1: sequence backing ConversationMessage.seq (created on fresh create_all AND in migration 0011).
_conv_msg_seq = Sequence("conv_msg_seq")


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# --- Identity & departments (SECURITY-RLS §2) ---
class Department(Base):
    __tablename__ = "departments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    sensitive: Mapped[bool] = mapped_column(default=False)  # HR/Accounting → pin local (egress)


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(default=False)
    # Effective permission strings, e.g. "doc:read:own_dept" (SECURITY-RLS §2.2)
    permissions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    # MCP token hash (HMAC-SHA256 + pepper) — plaintext never stored
    mcp_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    departments: Mapped[list[Department]] = relationship(
        secondary="employee_departments", lazy="selectin"
    )

    @property
    def department_ids(self) -> list[uuid.UUID]:
        return [d.id for d in self.departments]


class EmployeeDepartment(Base):
    __tablename__ = "employee_departments"
    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), primary_key=True
    )


# --- Knowledge sources & chunks ---
class Source(Base):
    __tablename__ = "sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(String(500))
    knowledge_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending|ready|failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # v2 three-tier visibility (ADR-0020, DOCUMENT-MANAGEMENT.md). Replaces the old
    # "empty departments == global" inference with an EXPLICIT column so a personal upload
    # (empty departments) is NOT global. FAIL-CLOSED default: personal (owner-only).
    #   personal   -> visible only to owner_id (+ admin). End-user chat uploads land here.
    #   department -> scoped via source_departments (tier B, existing mechanism).
    #   global     -> company-wide; requires an explicit doc:create:all publish.
    visibility: Mapped[str] = mapped_column(String(20), default="personal")
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("employees.id"), nullable=True, index=True
    )
    # SHA-256 of the uploaded bytes — scope-aware dedup (same hash + same scope => reuse).
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Departments scoping this source (tier B). Only meaningful when visibility='department'.
    departments: Mapped[list[Department]] = relationship(
        secondary="source_departments", lazy="selectin"
    )


class SourceDepartment(Base):
    __tablename__ = "source_departments"
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), primary_key=True
    )


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(_DIM))
    # Provenance (zero-hallucination — every number traceable)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cell_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    heading_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_table: Mapped[bool] = mapped_column(default=False)
    extra: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Denormalized scope for RLS-on-vector predicate pushdown (findings/J).
    # Mirrors source departments (tier B).
    department_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    # Denormalized visibility/owner mirroring the parent Source (v2, ADR-0020). RLS-on-vector
    # keys off these so a personal chunk never leaks via the old empty-array=global rule.
    visibility: Mapped[str] = mapped_column(String(20), default="personal")
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


# --- Drafts (non-invasive write path) & audit ---
class Draft(Base):
    __tablename__ = "drafts"
    # Idempotency (WP-E): cùng agent_run + payload_hash chỉ tạo MỘT draft (chống trùng khi resume).
    __table_args__ = (UniqueConstraint("agent_run_id", "payload_hash", name="uq_draft_run_hash"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String(50))  # journal_entry | wiki_edit | ...
    payload: Mapped[dict] = mapped_column(JSONB)
    payload_hash: Mapped[str] = mapped_column(String(64))  # pin args (findings/J anti-drift)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending|approved|rejected
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"))
    # RLS scope (WP-E): NULL = global; else list_pending lọc theo department người duyệt.
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentRun(Base):
    """Durable agent run — HITL paused-run resumable (WP-E / ADR-0010).

    Trên Postgres LỚP AI (KHÔNG chạm SQL Server ERP gốc — invariant #2). checkpoint_state lưu
    messages + retrieved-context + metric-results để resume DÙNG LẠI (cái human duyệt = cái thực
    thi), KHÔNG re-retrieve. lease_* chống 2 worker resume cùng run (Postgres-native, KHÔNG
    Temporal/Dapr — ADR-0013).
    """
    __tablename__ = "agent_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    status: Mapped[str] = mapped_column(String(40), default="running")
    # queued|planning|running|waiting_approval|completed|failed|cancelled. Legacy statuses
    # remain accepted during the strangler migration so existing run history stays readable.
    mode: Mapped[str] = mapped_column(String(30), default="auto")
    plan: Mapped[dict] = mapped_column(JSONB, default=dict)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    checkpoint_state: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Token usage THẬT của lượt (W1.2) — nền cho cost-tracking (W2.4). 0 nếu backend không trả
    # usage. routed_cloud/backend nằm trong checkpoint_state.
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    lease_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentRunEvent(Base):
    """Append-only, replayable client-safe progress events for a durable agent run."""
    __tablename__ = "agent_run_events"
    __table_args__ = (UniqueConstraint("agent_run_id", "seq", name="uq_agent_run_event_seq"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentApproval(Base):
    """Approval interruption independent of domain Draft approvals.

    A Draft remains the accounting-maker-checker artifact. This table is for any future SDK tool
    call that needs an explicit pause/resume decision (connector action, computer-use, export).
    """
    __tablename__ = "agent_approvals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    tool_name: Mapped[str] = mapped_column(String(120))
    args_hash: Mapped[str] = mapped_column(String(64))
    preview: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Artifact(Base):
    """Versioned, owner-scoped output produced by an agent run."""
    __tablename__ = "artifacts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"), index=True)
    kind: Mapped[str] = mapped_column(String(60))  # research_report | spreadsheet | chart | document
    title: Mapped[str] = mapped_column(String(300))
    mime_type: Mapped[str] = mapped_column(String(120), default="text/markdown")
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="ready")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --- Agent memory (lean MemGPT pattern — findings/J; rewritten from letta patterns) ---
class MemoryBlock(Base):
    """Core memory: in-context, agent-editable blocks (label -> value)."""
    __tablename__ = "memory_blocks"
    __table_args__ = (UniqueConstraint("session_id", "label", name="uq_block_session_label"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    label: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(Text, default="")
    char_limit: Mapped[int] = mapped_column(Integer, default=4000)


class ConversationMessage(Base):
    """Recall memory: conversation history.

    `trust_level` (WP-G): "trusted" for user/assistant turns the agent itself produced;
    "untrusted" for content derived from documents/ERP/tool-output that may carry
    injected instructions. The prompt builder frames untrusted content as DATA, never
    as behaviour-changing instructions (Invariant #1/#3). `source` records provenance.
    """
    __tablename__ = "conversation_messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    role: Mapped[str] = mapped_column(String(20))  # user|assistant|tool|system
    content: Mapped[str] = mapped_column(Text)
    trust_level: Mapped[str] = mapped_column(String(20), default="trusted")  # trusted|untrusted
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    feedback: Mapped[str | None] = mapped_column(String(10), nullable=True)  # like|dislike (P-chat)
    # P1: report-to-IT — optional free-text + category on a dislike (see routes feedback).
    feedback_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # P1: absolute per-table ordering (tie-free) for truncate/edit (P3) — sequence-backed.
    seq: Mapped[int] = mapped_column(
        BigInteger, _conv_msg_seq, server_default=_conv_msg_seq.next_value(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base):
    """Hội thoại chat (P-chat) — gom các ConversationMessage cùng session thành 1 thread
    có chủ sở hữu + tiêu đề. `id` == session_id (1:1, tái dùng key sẵn có). RLS THEO NGƯỜI
    DÙNG: chỉ chủ sở hữu (employee_id) thấy hội thoại của mình; chia sẻ read-only qua
    shared_token (link không đoán được). Khác RLS dept-scope của chunks."""
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)  # == session_id
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True)
    shared_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)


class Attachment(Base):
    """Chat-message attachment (v2 Track 3) — NOT vectorized (DocsGPT pattern).

    An attachment is strictly PERSONAL: owner-only, gated in SQL by owner_id (admin bypass).
    `kind` splits the chat handling: image -> multimodal base64 to the vision LLM; text ->
    extracted `content` injected into the prompt (framed as DATA). Oversized text falls back
    to RAG: a personal Source is created and `source_id` links it (retrieved via the normal
    personal-tier chunk scope).
    """
    __tablename__ = "attachments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"), index=True)
    # Bound at first chat use so the attachment is reusable across the conversation's turns.
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(1000))
    kind: Mapped[str] = mapped_column(String(20), default="text")     # image | text
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|ready|failed
    content: Mapped[str | None] = mapped_column(Text, nullable=True)   # extracted text (kind=text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # P1: bound to the user ConversationMessage this attachment was sent with (last-N-turn image
    # re-send + truncate/erasure). ON DELETE SET NULL so truncating a turn doesn't orphan-block.
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversation_messages.id", ondelete="SET NULL"), nullable=True, index=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ArchivalPassage(Base):
    """Archival memory: long-term, vector-searchable. Scoped for RLS like chunks.

    Passages are almost always derived from external documents/ERP, hence default
    `trust_level="untrusted"`: their content must be framed as DATA when recalled into
    a prompt, never obeyed as instructions (memory-poisoning defense — WP-G).
    """
    __tablename__ = "archival_passages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(_DIM))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    department_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    # WP-G: archival content is document/ERP-derived -> untrusted by default.
    trust_level: Mapped[str] = mapped_column(String(20), default="untrusted")  # trusted|untrusted
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (UniqueConstraint("id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    action: Mapped[str] = mapped_column(String(200))
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ToolCallAttempt(Base):
    """Nhật ký tool-call (compliance/observability — pattern DocsGPT tool_executor).

    Mỗi lần agent gọi tool ghi MỘT dòng: drafted (ghi->nháp) | executed (đọc ok) | failed.
    `args_hash` pin tham số (không lưu nội dung nhạy thô); `agent_run_id` truy vết theo lượt.
    """
    __tablename__ = "tool_call_attempts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    tool: Mapped[str] = mapped_column(String(100))
    args_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20))  # drafted|executed|failed
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
