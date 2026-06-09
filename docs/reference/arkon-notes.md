# Arkon — Reference Notes

**Là gì:** Enterprise Knowledge Base RAG, production-grade. **Vai trò với BRAVO:** bộ xương an ninh & tri thức. Đây là repo *gần nhất* với BRAVO AI Copilot về tư duy — ưu tiên học kỹ.

**Stack:** FastAPI + async SQLAlchemy · PostgreSQL 16 + pgvector · Redis + arq (worker) · MinIO · FastMCP · Next.js. LLM/embedding đa nhà cung cấp (gồm Ollama cục bộ).

---

## 1. RLS / RBAC — *điểm vàng để học* ⭐

**Dual-realm:** (a) quyền theo phòng ban `{resource}:{action}:{scope}` với scope `own_dept`/`all`; (b) quyền theo workspace/dự án (membership role).

**Cưỡng chế ở tầng SQL — không lọc trong RAM:**
- `app/services/auth_service.py` — `require_permission()` dependency cho route.
- `app/services/permission_engine.py` — `can_access_document()`, **`build_document_filter()`** trả về điều kiện lọc dựng *trong* truy vấn.
- Quy tắc gắn nhãn: **source 0 phòng ban = global**; n phòng ban = OR scope.

```python
# build_document_filter → WHERE: (source không có phòng ban) OR (phòng ban ∈ allowed)
stmt = stmt.where(or_(
    ~exists(select(1).select_from(SourceDepartment).where(...)),   # global
    SourceDepartment.department_id.in_(allowed_dept_ids),
))
```

**Lấy cho BRAVO:** sao chép y nguyên triết lý "filter trong SQL"; mở rộng `resource` cho `erp`/`analytics`; thêm chiều scope đơn-vị/kỳ cho số liệu.

## 2. MCP scoped-by-token
- `app/services/mcp_auth_service.py` — `ResolvedIdentity` (employee, department_ids, allowed_source_ids, permissions, is_admin); `verify_token()` dùng **HMAC-SHA256 + pepper**, không lưu plaintext; `apply_scope_filter(query, identity)` ghép scope vào mọi truy vấn tool.
- `app/mcp/tools.py` (~1980 dòng) — catalog tool theo tier (read → contribute → edit → review). Mỗi tool tự áp scope.
- `app/mcp/middleware.py` — lọc `tools/list` theo quyền (UX, **không** phải biên an ninh; kiểm tra thật nằm trong thân tool).
- **Out-of-scope hint** (`_format_oos_hint`): chỉ lộ loại-scope + số lượng, **không bao giờ** tiêu đề.

**Lấy cho BRAVO:** mô hình token + scope này là chuẩn để tích hợp Claude/Copilot ngoài mà vẫn giữ RLS.

## 3. Workflow nháp → duyệt ⭐
- Models: `WikiPageDraft` (status: pending/needs_revision/withdrawn/approved/rejected; `draft_kind` edit/create; `ai_check_status`), `WikiPageRevision` (lịch sử bất biến).
- `app/routers/wiki_drafts.py` (~1138 dòng) — propose → AI pre-review (4 lớp: regex/structural/semantic/LLM) → review → approve/reject/request-changes → resubmit/withdraw.
- **Duyệt dùng advisory-lock** (`pg_advisory_xact_lock(hashtext(slug))`) chống race; refresh trong vùng tới hạn; tạo revision bất biến.

**Lấy cho BRAVO:** đây là khuôn mẫu cho **Draft Queue** nghiệp vụ ERP — kể cả pattern AI pre-review trước khi người duyệt, và advisory-lock.

## 4. Pipeline biên soạn có trích dẫn (MRP)
- `app/ai/mrp/` — Map (trích entity/claim kèm `absolute_offset` về nguồn) → Reduce (dedup bằng embedding + plan) → **Human review plan** → Refine (writer sinh markdown với footnote `[^N]`) → **Verify** (đối chiếu từng `[^N]` với excerpt nguồn; phát hiện mâu thuẫn) → Commit (upsert + embedding, transaction atomic).
- Mỗi phase ghi trạng thái DB ⇒ **crash-resumable**.

**Lấy cho BRAVO:** bước **Verify** là vũ khí chống ảo tưởng; "human review plan" là điểm chèn người duyệt; resumable là bài học vận hành.

## 5. Cấu trúc & vận hành
- `app/routers/` (REST) · `app/services/` (logic + `ai_review/` 4 lớp) · `app/ai/mrp/` · `app/mcp/` · `app/worker.py` (arq, 2 pool: wiki + skill, có cron).
- `docker-compose.yml`: 7 container (postgres, redis, minio, api, worker×2, frontend).
- Embedding **đa chiều** (768/1024/1536/3072) — bảng riêng mỗi chiều để đổi model không re-index toàn bộ.

## 6. Tài liệu đáng đọc trong arkon
`docs/ACCESS-CONTROL.md` (RBAC), `docs/MCP.md` (tool reference), `docs/WIKI.md` (MRP), `docs/ARCHITECTURE.md`, `DESIGN.md` (hệ design "Sahara").

---
## ✅ Việc cần làm khác đi cho BRAVO
- Thêm chiều scope **đơn vị cơ sở / kỳ kế toán** cho dữ liệu ERP (arkon chỉ có phòng ban/workspace).
- Gắn RLS vào **ERP read tools**, không chỉ tài liệu.
- Draft Queue đẩy về **giao diện ERP BRAVO**, không phải wiki nội bộ.
