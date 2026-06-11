# WP-E — AgentRun durable + draft-queue hardening (HITL paused-run)

> Module: `app/database`, `app/erp`. **Đọc [CONTRACTS.md](CONTRACTS.md) trước.** Phụ thuộc: CONTRACTS (AgentRun, Draft).

## Mục tiêu
Lấp khoảng trống "không có agent-run/job model": **HITL paused-run resumable** + **draft-queue an toàn** (chống double-posting, self-approval, rò scope). Postgres-native, **không** Temporal/Dapr.

## Reuse (ADR-0013)
REWRITE-LEAN trên Postgres lớp AI. Lấy **pattern** checkpointer (LangGraph làm blueprint) nhưng tự xây — **không cài** LangGraph Platform (egress beacon). Hash-pin anti-drift ([draft_queue.py:47-48]) đã đúng — giữ.

## Scope IN / OUT
**IN:** ORM `AgentRun` (CONTRACTS §2.6) trên Postgres lớp AI; `create_draft` **idempotent** (UNIQUE `idempotency_key`/`agent_run_id+payload_hash`, `ON CONFLICT DO NOTHING`); `approve_draft` với **advisory-lock** (`pg_advisory_xact_lock`) + **chặn self-approval** (`created_by==approver`) + **require `draft:approve`** + audit; `list_pending` lọc **RLS theo department**; snapshot context/metric vào `checkpoint_state` để resume **dùng lại** (không re-retrieve); lease/lock per `agent_run_id` chống 2 worker resume đôi.
**OUT (đừng làm):** push draft sang ERP staging (deferred — chưa có endpoint); journal-entry validator (Phase 3); Temporal/Dapr; supervisor phức tạp (cron quét lease quá hạn là đủ).

## Files
`app/database/models.py` (AgentRun + mở rộng Draft: `department_id/created_by/agent_run_id/status`) · `alembic/` (migration) · `app/erp/draft_queue.py` (hardening) · `app/api/routes_drafts.py` (perm + RLS).

## Việc cụ thể
1. ORM `AgentRun` + mở rộng `Draft` theo CONTRACTS §2.6; migration.
2. `create_draft(db, identity, kind, payload, agent_run_id)`: tính `payload_hash`; UNIQUE(`agent_run_id`,`payload_hash`) + `ON CONFLICT DO NOTHING` (resume không tạo trùng); set `created_by=identity.employee_id`, `department_id`.
3. `approve_draft(db, identity, draft_id)`: `pg_advisory_xact_lock(hashtext(draft_id))`; nếu `draft.created_by==identity.employee_id` và không cho self-approval → 403; require `identity` có `draft:approve`; verify `payload_hash` không đổi; set `approved`.
4. `list_pending(db, identity)`: lọc `department_id` theo scope identity (RLS trong SQL).
5. `save_checkpoint/resume`: lưu/đọc `checkpoint_state` (messages + retrieved-context + metric-results); lease (`lease_owner/expires`) `FOR UPDATE SKIP LOCKED`.

## Acceptance (test)
- self-approval (created_by==approver) → từ chối.
- 2 lời `approve_draft` đồng thời cùng draft → serialize (1 thắng, 1 thấy đã approved).
- user thiếu `draft:approve` → 403.
- `list_pending` của phòng A KHÔNG thấy draft phòng B.
- resume cùng `agent_run_id` → `create_draft` không tạo bản trùng (ON CONFLICT).

## Invariant
#1 (list_pending RLS) · #2 (maker-checker, draft là ranh giới ghi duy nhất, idempotent, không chạm ERP gốc).

## Phụ thuộc
CONTRACTS (AgentRun, Draft). WP-D gọi `create_draft`; build song song dùng stub.
