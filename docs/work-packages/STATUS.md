# STATUS — bảng điều phối work-package (cho các chat song song)

> **Mục đích:** mọi Claude chat làm song song xem ĐÂY để biết gói nào đã nhận / đang làm / xong, tránh đụng nhau.
> **Trước khi bắt đầu một gói:** sửa dòng của gói đó → đặt 🔄 + tên chat của bạn. Khi xong → ✅ + commit ref.
> **Branch:** `feat/agentic-demo`. Rebase lên commit mới nhất ở cột Commit trước khi code.
> **Interfaces giờ là CODE THẬT** (không còn stub): `MetricResult`/`verify_numbers` (WP-B), `classify_context` (WP-C), `MockDataSource`/`DataSource.fetch(...identity)` (WP-F) — đọc [CONTRACTS.md](CONTRACTS.md).

## Bảng tiến độ

| Gói | Trạng thái | Chat/Owner | Commit | Verify | Ghi chú |
|---|---|---|---|---|---|
| **WP-B** Verify-gate | ✅ DONE | chat-chính | `267aec2` | 38 tests | money.py·MetricResult·grounding bắt tỷ↔triệu |
| **WP-C** Egress | 🟡 CORE DONE | chat-chính | `267aec2` | tests | `classify_context` xong; **router audit-then-egress còn lại** → gộp WP-D |
| **WP-F** Mock+semantic-RLS | ✅ DONE | chat-chính | `1e58848` | 38 tests | MockDataSource·RLS số·scope_columns fail-at-load |
| **WP-E** AgentRun+draft | ✅ DONE | chat-chính | `3d2f72a` | DB smoke + 5 tests | AgentRun ORM·migration `0003` (đã áp DB)·anti-self-approval·advisory-lock·list_pending RLS·idempotency — verify trên Postgres THẬT |
| **WP-A** Ingestion Docling | 🔄 IN-PROGRESS | **chat-opus** | — | — | Docling chưa cài (máy yếu) → code + test `importorskip`; pypdf giữ chạy; nạp `file_system/` |
| **WP-D** Agent loop | ✅ CODE DONE (chưa commit) | **chat-opus** | — | 16 tests | loop.py+tools.py Pydantic AI+Budget. **Wire khi integrate:** `router.chat(context=)` [WP-C], thay stub→`semantic.answer` [WP-F THẬT], `frame_untrusted` [WP-G] |
| **WP-G** RLS+memory | ✅ CODE DONE (chưa commit) | **chat-opus** | — | 14 tests | memory.py·rls.py(`frame_untrusted`)·**models.py +trust_level/source**·**migration `0002_memory_trust` (đã áp DB)** |
| **WP-H** Eval pass^k | 🔄 IN-PROGRESS | **chat-opus** | — | — | golden trajectory·pass^k·HARD-FAIL CI (stub-tolerant) |

**Chú thích:** ✅ DONE · 🔄 IN-PROGRESS (có người làm) · 🟡 PARTIAL · ⬜ TODO · 🔒 BLOCKED.

## Quy ước để không đụng nhau
- **Chỉ sửa file trong Scope của gói mình** (xem mỗi WP-x.md). Đụng file gói khác → chỉ qua interface ở CONTRACTS.
- Gói có 🔄 = **đã có người làm**, đừng nhận lại. Nhận gói ⬜ → đổi thành 🔄 + tên chat **trước khi** code.
- Xong gói → chạy `pytest -q` xanh → commit → cập nhật dòng (✅ + commit) → báo chat điều phối.
- **Đừng** commit `file_system/` (corpus 129MB, đã gitignore) hay đụng việc xoá `UserGuide_B10_TV_PDF/` cũ.

## Nhật ký điều phối (đọc để biết file dùng chung)
- **`3d2f72a` (WP-E)** đã commit kèm **nền DB dùng chung** vì `0003` nối sau `0002`: `app/database/models.py` (gồm cả `trust_level/source` của **WP-G**) + `alembic/versions/0002_memory_provenance_trust.py` (WP-G) ĐÃ NẰM TRONG commit này để HEAD có **migration chain hợp lệ**. → **chat-opus (WP-G):** commit của bạn chỉ cần thêm `app/agent/memory.py` + `app/security/rls.py` (`frame_untrusted`) + test WP-G; models.py/0002 đã committed (git sẽ tự thấy unchanged).
- **DB đang chạy** (`bravo-postgres-1`), head = `0003_agentrun_draft`. Chạy `alembic upgrade head` sau khi rebase.
- **WP-C còn lại** (router `chat(context=)` audit-then-egress) CHƯA làm — WP-D đang gọi qua **stub**; cần ai đó (gộp WP-D hoặc WP-C) wire thật trước khi demo egress.

## Việc Deferred (đừng làm ở demo)
ERP client thật · local Qwen + guided decoding + air-gapped packaging · Phase 3 push-to-ERP · Temporal/Dapr · LangGraph Platform. (Xem [AGENTIC-PLAN §Deferred](../AGENTIC-PLAN.md).)
