# Prompt khởi động cho từng work-package (dán vào mỗi Claude chat)

> Mỗi gói = một chat độc lập. Dán nguyên prompt dưới vào chat tương ứng. Mọi chat đều bắt đầu bằng đọc [CONTRACTS.md](CONTRACTS.md).
> Lưu ý chung dán kèm mọi chat: *"Chỉ sửa file trong Scope của gói. Phụ thuộc gói khác chỉ dùng qua interface ở CONTRACTS (viết stub nếu cần). Tôn trọng 4 nguyên tắc bất biến + lằn ranh chống over-engineering ở CONTRACTS §5. Viết test cùng code; acceptance ở spec phải xanh. CHƯA commit."*

---

### WP-A — Ingestion Docling
```
Đọc d:/Tien/Workspace/bravo/docs/work-packages/CONTRACTS.md và WP-A-ingestion-docling.md.
Implement WP-A: dùng Docling (dep chính, do_table_structure=True, do_ocr=False) cho PDF-có-bảng/DOCX/XLSX,
giữ pypdf fast-path cho PDF text-thuần; điền provenance page/sheet/cell từ Docling TableItem.prov.
Nạp corpus Demo A trong d:/Tien/Workspace/bravo/file_system/. Viết test theo mục Acceptance. Chưa commit.
```

### WP-B — Verify-gate
```
Đọc CONTRACTS.md và WP-B-verify-gate.md. Implement: MetricResult value-object (Decimal+scale),
verify_numbers scale-aware (chặn tỷ↔triệu) + safe_answer (mask), Decimal cho tiền + reconcile.
KHÔNG wire vào loop (việc WP-D). Test theo Acceptance. Chưa commit.
```

### WP-C — Egress
```
Đọc CONTRACTS.md và WP-C-egress-router.md. Implement classify_context (tự phân loại từ nhãn nguồn,
unknown->local) + router.chat audit-then-egress (ghi AuditLog TRƯỚC khi gọi cloud, fail-closed).
Bỏ mọi đường truyền sensitive thủ công. Test theo Acceptance. Chưa commit.
```

### WP-D — Agent loop
```
Đọc CONTRACTS.md và WP-D-agent-loop.md. Implement single-agent ReAct loop ngắn (control-flow trong code)
trên Pydantic AI cho structured tool-output; tool schema + filter_tools_by_permission + call_tool (RLS lần 2,
write->draft) + Budget circuit-breaker + clarify; gọi verify_numbers (WP-B) + router.chat(context=) (WP-C).
Dùng stub cho WP-B/C/E theo chữ ký CONTRACTS §3.1. Test theo Acceptance. Chưa commit.
```

### WP-E — AgentRun + draft hardening
```
Đọc CONTRACTS.md và WP-E-agentrun-draft.md. Implement ORM AgentRun + mở rộng Draft
(department_id/created_by/agent_run_id), migration; draft_queue: advisory-lock + anti-self-approval +
draft:approve permission + list_pending RLS + idempotency (ON CONFLICT). Test theo Acceptance. Chưa commit.
```

### WP-F — Mock + semantic-RLS
```
Đọc CONTRACTS.md, WP-F-mock-semantic.md, MOCK-DATA-SPEC.md. Implement MockDataSource đọc
tests/fixtures/mock_financials_tt99.yaml trả MetricResult (WP-B), DataSource.fetch(...identity) áp RLS,
metric registry fail-at-load nếu thiếu scope_columns, variants + clarify + reconcile, ngoài whitelist->ABSTAIN.
Test theo Acceptance. Chưa commit.
```

### WP-G — RLS + memory hardening
```
Đọc CONTRACTS.md và WP-G-rls-memory-hardening.md. Implement: trust_level/source cho ConversationMessage+
ArchivalPassage + đóng khung untrusted; sửa _archival_scope dùng func.cardinality()==0; doc DB-role SELECT-only
+ statement_timeout; khẳng định không đường nào để LLM sinh SQL tự do. Test theo Acceptance. Chưa commit.
```

### WP-H — Eval pass^k
```
Đọc CONTRACTS.md, WP-H-eval-passk.md, AGENTIC-SPIKE-WS0.md. Implement golden-trajectory schema +
~30-50 mục tiếng Việt + pass^k runner (k>=8) qua AgentSession.step() + tập HARD-FAIL (RLS-leak/bịa-số/
sai-đơn-vị/egress) + CI gate. Viết stub-tolerant (mock loop) để chạy độc lập. Test theo Acceptance. Chưa commit.
```
