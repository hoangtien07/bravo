# USECASE-INVENTORY — Use-case chuẩn cho BRAVO AI Copilot (grounded từ code + corpus)

> Nguồn sự thật cho câu hỏi "hệ thống phục vụ use case nào, trên corpus nào, chín tới đâu".
> Grounded từ code branch `feat/v2-p0-containment` + manifest ingestion, **không nói theo tài liệu cũ**.
> Ngày: 2026-07-20 · Liên quan: [ADR-0031](adr/0031-first-pilot-ap-vertical-gate.md) (pilot), [PILOT-U2-SCOPE.md](PILOT-U2-SCOPE.md), [VISION.md §5](VISION.md), [MATURITY-LADDER.md](MATURITY-LADDER.md).

## 0. Đính chính so với inventory thảo luận trước (2026-07-20)

Bản inventory đầu tiên mô tả corpus tri thức là **"19 chương user-guide"** — **SAI phạm vi**. Corpus thực tế
đã nạp là **corpus hỗn hợp ~72 nguồn / 3141 chunk** gồm **ba loại tài liệu phục vụ ba đối tượng khác nhau**;
user-guide chỉ là ~26% số nguồn, còn **KQPT/PTNV chiếm 41% chunk-volume** ([bravo_intent.py:151](../app/rag/bravo_intent.py#L151)).
Retriever kéo **xuyên cả ba corpus** theo `lifecycle_stage` ([bravo_intent.py:82,90,114](../app/rag/bravo_intent.py#L82)).

## 1. Corpus đã nạp (nguồn sự thật = `file_system/bravo_corpus_manifest.yaml`)

Ingestion là **manifest-driven** — chỉ file khai trong manifest mới vào corpus GLOBAL (chống rò file demo/private).
Script: [scripts/ingest_userguide.py](../scripts/ingest_userguide.py).

| Thư mục `file_system/` | `source_type` | Số nguồn | Đối tượng phục vụ | Bản chất tài liệu |
|---|---|---|---|---|
| `UserGuide_B10_TV_PDF/` | `user_guide` | 19 | End-user / helpdesk | Hướng dẫn sử dụng 19 chương |
| (mindmap dẫn xuất `.md`) | `mindmap` | 19 | Điều hướng/tra cứu cấu trúc | Sơ đồ tư duy theo phân hệ |
| `KQPT_PTNV/` | `kqpt_ptnv` | 20 | **BA/PTNV · product · QA** | Kết quả phân tích nghiệp vụ (IFRS, QLCV, 2FA, KiemKe, DanhGia NCC…) |
| `TaiLieuKyThuat_Dll/` | `technical_manual` | 11–12 | **Dev · kỹ thuật triển khai** | Tài liệu kỹ thuật DLL (Reporter, Datasource, USPCaller, TaskMan, Dashboard, Explorer…) |
| (khác) | `report_template`, `basic_rule` | 2 | Kế toán/cấu hình | BI Guidelines, Basic rules |

**Tổng:** ~72 nguồn, 3141 chunk. **KQPT/PTNV = 41% chunk-volume** (phần lớn nhất, không phải user-guide).

## 2. Use-case inventory (phân loại + trạng thái)

**Thang điểm:** Giá trị / Tần suất / Khả thi-ngay (data thật + wired + không đóng băng) — 1–5.
**Phân loại:** RAG thuần (retrieve+cite, không hành động) · Agent-tool (nhiều bước, tool tất định) · Agent-write (tạo nháp + maker-checker).

| # | Use case | Corpus/Data | Phân loại | GT | TS | KT | Trạng thái (code) |
|---|---|---|:-:|:-:|:-:|:-:|---|
| **U1a** | Hỏi-đáp **end-user/helpdesk** | user_guide + mindmap ✅THẬT | RAG thuần | 4 | 5 | 5 | [grounded_answer.py:42](../app/rag/grounded_answer.py#L42) — chạy E2E |
| **U1b** | Trợ lý **kỹ thuật/dev** (DLL) | technical_manual ✅THẬT | RAG thuần | 3 | 3 | 4 | Chung retrieval path; định tuyến [bravo_intent.py:114](../app/rag/bravo_intent.py#L114) |
| **U1c** | Trợ lý **BA/PTNV/QA** (vòng đời) | kqpt_ptnv (41%) ✅THẬT | RAG thuần (+U6) | 3 | 3 | 4 | Chung retrieval path; định tuyến [bravo_intent.py:90](../app/rag/bravo_intent.py#L90) |
| **U2** | **Copilot AP**: hoá đơn→định khoản nháp→maker-checker→xuất Excel | Hoá đơn upload ✅THẬT | Agent-write | 5 | 3 | 5 | [ap_service.py](../app/accounting/ap_service.py) — **PILOT đóng cổng** ([ADR-0031](adr/0031-first-pilot-ap-vertical-gate.md)) |
| U3 | Hỏi-đáp **số liệu tài chính** NL | ❌MOCK (chờ `BravoErpDataSource`) | Agent-tool | 5 | 4 | 1 | [semantic.py:97](../app/data_layer/semantic.py#L97) — code thật, data mock |
| U4 | Phát hiện **bất thường** | ❌MOCK | Agent-write | 5 | 2 | 1 | [anomaly.py](../app/agent/anomaly.py) — 🧊 đóng băng tới L3 |
| U5 | Đối chiếu **thuế** VAT↔tờ khai | ❌MOCK | Agent-write | 4 | 2 | 1 | [tax.py](../app/agent/tax.py) — 🧊 đóng băng |
| U6 | **Consultant Intelligence** (scaffolding vòng đời) | catalog+KEDB ✅THẬT (OFF) | Agent-tool | 3 | 3 | 3 | [consultant/service.py](../app/consultant/service.py) — `enabled=False` |
| U7 | Báo cáo quản trị NL (D) / cross-source (E) | — | Agent-tool | 3 | 2 | 1 | Chưa build thực chất |

### "Có đúng là bài toán agent không?"
- **U1a/b/c KHÔNG phải bài toán agent** — RAG thuần, không cần loop/tool. Ba use case chỉ khác **đối tượng + corpus**, dùng chung một retrieval path (định tuyến theo `lifecycle_stage`). Gap chất lượng là recall+prompt, không phải framework ([[bravogen-gap]]).
- **U2 MỚI là bài toán agent-write** — tool tất định + maker-checker + HITL. Đây là nơi "agent" có lý do tồn tại → chọn làm pilot.
- **U3/U4/U5** là agent hợp lệ nhưng **bất khả thi ngay** (mock, chờ ERP API).

## 3. Rủi ro/ghi chú cần theo dõi (grounded)

1. **Corpus-mix bias:** KQPT chiếm 41% → [bravo_intent.py:151-165](../app/rag/bravo_intent.py#L151) phải **demote `kqpt_ptnv`** cho câu how-to end-user, nếu không câu trả lời "đọc như phân tích hệ thống" thay vì hướng dẫn thao tác. ⇒ Tiêu chí cổng U1 phải đo **recall tách theo từng `source_type`**, không gộp.
2. **Egress theo độ nhạy corpus:** user_guide ~công khai; **kqpt_ptnv + technical_manual chứa phân tích/kỹ thuật nội bộ** — quyết định rõ loại nào được egress ra cloud (blocker SEC-C1, xem [PILOT-U2-SCOPE.md §6](PILOT-U2-SCOPE.md)).
3. **Manifest = ranh giới an ninh:** chỉ file trong manifest vào corpus GLOBAL; file ngoài manifest bị bỏ qua (chống rò private). Giữ nguyên tắc này khi mở rộng corpus.

## 4. Ánh xạ đối tượng ↔ use case (cho BA)

| Đối tượng nội bộ BRAVO | Use case | Corpus chính |
|---|---|---|
| Helpdesk / cán bộ triển khai (tra cứu vận hành) | U1a | user_guide, mindmap |
| Dev / PTSP / kỹ thuật | U1b (+U6) | technical_manual |
| BA / PTNV / QA (vòng đời phần mềm) | U1c (+U6) | kqpt_ptnv |
| Kế toán AP (nhập liệu chứng từ) | **U2** | Hoá đơn upload |
| Lãnh đạo/CFO (số liệu, giám sát) | U3/U4/U5 | ❌ chờ ERP data thật |
