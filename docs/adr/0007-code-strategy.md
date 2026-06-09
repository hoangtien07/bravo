# 0007. Chiến lược code: lõi greenfield hợp nhất, modular-monolith; mượn pattern/chuyển thể có chọn lọc

- **Trạng thái:** Accepted
- **Ngày:** 2026-06-08
- **Người quyết định:** Đội dự án BRAVO AI Copilot
- **Liên quan:** [ADR-0002](0002-architecture-as-synthesis-of-three-repos.md) (tổng hợp pattern), [ADR-0008](0008-arkon-license-ownership.md) (giấy phép arkon — gating), [ARCHITECTURE](../ARCHITECTURE.md).

## Bối cảnh (Context)
Câu hỏi: với phần tham chiếu 3 repo, nên (A) viết mới từ đầu, (B) fork 3 repo thành microservices ghép lại, hay (C) hybrid? Yếu tố quyết định mới:
- **Giấy phép:** arkon = **PolyForm Internal Use 1.0.0** (cấm đóng gói vào sản phẩm phân phối/bán); docsgpt = **MIT**; letta = **Apache 2.0**.
- **3 framework khác nhau:** arkon (FastAPI), docsgpt (Flask), letta (FastAPI).
- **Triển khai on-prem air-gapped** cần cài đơn giản (Track C: dự án GenAI chết vì quá phức tạp).
- **RLS mạnh nhất khi lọc trong 1 câu SQL ở 1 tầng dữ liệu** (Track J: lọc trong query = 0% rò; phân tán = bề mặt rò tăng).

## Các phương án (Options)
1. **Viết mới hoàn toàn.** Sạch nhưng giải lại bài khó (RLS, parse bảng) → chậm.
2. **Fork 3 repo thành microservices.** Nhanh lúc đầu nhưng: 3 framework + 3 mô hình bảo mật ghép = địa ngục tích hợp; **RLS phân tán** phá nguyên tắc #1; gánh nợ kỹ thuật repo ngoài; **vi phạm giấy phép arkon**; air-gapped khó cài. **Bị loại.**
3. **Hybrid: lõi greenfield hợp nhất (1 framework, 1 mô hình bảo mật) + mượn pattern/chuyển thể module có chọn lọc; modular-monolith trước.**

## Quyết định (Decision)
Chọn **Phương án 3**.

**Stack nền:** **FastAPI + async SQLAlchemy + PostgreSQL/pgvector** (2/3 repo đã dùng → tái hiện pattern & chuyển thể dễ nhất; ingestion docsgpt độc lập framework nên bóc ra được).

**Hình thái triển khai:** **modular monolith** (1 ứng dụng lõi, module ranh giới rõ) + vài service hạ tầng tách sẵn vì bản chất: ① LLM server (vLLM/Ollama), ② ingestion worker (nặng, async), ③ Postgres+pgvector, ④ frontend. **Tách thêm service chỉ khi quy mô đòi hỏi** (YAGNI).

**Bản đồ lấy gì từ đâu (đã tính giấy phép):**
| Thành phần | Nguồn | Cách làm |
|-----------|-------|----------|
| RLS/permission engine, MCP, draft workflow, MRP | arkon | **Học PATTERN, viết lại** (PolyForm cấm ship code) |
| Ingestion (Docling, chunking), abstraction LLM/vector, ingest resumable | docsgpt (MIT) | **Chuyển thể CODE** → thư viện/worker, bọc lại |
| Bộ nhớ agent (lõi gọn), tool sandbox, requires_approval | letta (Apache 2.0) | **Chuyển thể CODE có chọn lọc** (không bê full framework — xem [findings/J §3](../research/findings/J-rag-agent-eval.md)) |
| Semantic layer, Calc layer, Draft Queue, Model Router, ERP client, provenance trang/ô, eval tiếng Việt, TT 99 | BRAVO | **Code mới** (phần độc quyền) |

## Hệ quả (Consequences)
- Tích cực: kiến trúc hợp nhất, bảo mật-mặc-định, RLS tập trung; tái dùng phần khó ở mức module; cài air-gapped đơn giản; tuân thủ giấy phép.
- Tiêu cực/nợ: cần công sức "keo" + thích nghi code; viết lại pattern arkon thay vì copy; phải chuẩn hoá khi tái hiện từ 3 stack khác nhau.
- Phụ thuộc: **[ADR-0008]** xác nhận quyền sở hữu/giấy phép arkon (nếu VHV/BRAVO sở hữu arkon thì có thể chuyển thể trực tiếp thay vì viết lại).
- Việc tiếp: dựng skeleton lõi; định nghĩa ranh giới module; chuyển thể ingestion docsgpt đầu tiên (đường tới MVP).

## Tham chiếu
[ADR-0002](0002-architecture-as-synthesis-of-three-repos.md), [reference/](../reference/), [findings/J](../research/findings/J-rag-agent-eval.md).
