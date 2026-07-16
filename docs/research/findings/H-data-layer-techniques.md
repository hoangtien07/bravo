# Findings H — Tầng số liệu: NL2SQL an toàn, Semantic Layer, Table-RAG (deep-dive kỹ thuật)

> Lấp khoảng trống "how" của [ADR-0004](../../adr/0004-llm-never-computes-numbers.md) (LLM không tính số) & [ADR-0005](../../adr/0005-no-free-form-sql.md) (không SQL tự do). Agent đọc nguồn gốc arXiv/ACL + tài liệu sản phẩm, 2026-06-08. Phân biệt [FACT]/[suy luận]/KXM.

## 0. Kết luận: cả 2 ADR được hậu thuẫn mạnh
- **ADR-0005 (metric layer)** là **cách duy nhất hiện có** đạt độ chính xác ~100% *trong phạm vi đã model* + chống fan-out theo cấu trúc.
- **ADR-0004 (deterministic calc, PAL/PoT)** là pattern **đã chứng minh trên chính domain tài chính**.
- Hai rủi ro phải thiết kế chủ động: **provenance** (không có chuẩn) và **abstention** (chưa giải được ở tầng model → làm ở tầng hệ thống).

## 1. Semantic / Metric Layer (xương sống ADR-0005)
- **Nguyên lý:** LLM chỉ map câu hỏi → `(metric, dimension, filter, time grain)`; **engine (dbt MetricFlow / Cube) sinh SQL deterministic** → LLM **không thể** tạo join/aggregation sai, **không thể** ra số "đúng kiểu nhưng lệch giữa các lần chạy".
- **Bằng chứng (vendor, chỉ dấu xu hướng):** dbt 2026 — trong phạm vi semantic layer **đạt ~100%** (vs text-to-SQL 84–90%); quan trọng hơn: *"semantic layer BÁO không trả lời được — không bao giờ trả số sai; text-to-SQL thì vui vẻ đưa số sai."* Cube: có semantic layer thì **chọn model nào cũng được** mà không mất accuracy.
- **Fan-out/chasm join** (đếm trùng — vd báo "$300 cho 4 món" thay vì $100) được xử lý ở tầng này: entity-type-aware join + pre-aggregation CTE + symmetric aggregate + EXPLAIN-validate trước khi chạy.
- **Công cụ:** **Cube** ưu tiên (API-first, **có MCP cho agent**, embedded, **Brex & Drata đã dùng cho "AI financial analyst"**); dbt MetricFlow là lớp định nghĩa metric. Chuẩn portability mới: OSI (Open Semantic Interchange).
- ⚠️ **Trần năng lực:** semantic layer chỉ trả lời câu hỏi *trong phạm vi đã model* → "độ biểu đạt của semantic layer = trần những gì AI trả lời tin cậy được". Ngoài phạm vi → phải **từ chối**, không rơi xuống SQL tự do.

## 2. Deterministic computation — PAL/PoT (xương sống ADR-0004)
- **PAL** (arXiv:2211.10435, ICML 2023) & **PoT** (arXiv:2211.12588): LLM sinh *chương trình* làm bước suy luận, **interpreter (Python/SQL) thực hiện phép giải**; exemplar **không chứa đáp số cuối** → LLM **không bao giờ tự sinh số cuối**.
- **Hiệu quả tài chính:** PoT trên FinQA/ConvFinQA/TATQA **hơn CoT ~12%** trung bình (xác nhận từ repo TIGER-AI-Lab). PAL hơn CoT ~40% trên bài số lớn.
- **Hạn chế:** chỉ áp cho bài biểu diễn được bằng code; **rủi ro thực thi code độc** → cần **sandbox không quyền ghi**.
- **Pattern BRAVO:** số chính do SQL/metric tính; phép phái sinh (YoY, biên LN, tỷ lệ) dùng **PoT/PAL trong sandbox**; LLM **tuyệt đối không xuất số cuối** trong free text.

## 3. Table-RAG (bóc tách & truy hồi bảng)
- **Vấn đề:** RAG chuẩn đọc PDF tuyến tính → **phá cấu trúc bảng** (mất quan hệ cell–header).
- **TableRAG (NeurIPS 2024, Google, arXiv:2410.04739):** **schema retrieval** (nhận cột quan trọng + min/max/giá trị mẫu) + **cell retrieval** (encode từng cell distinct) → giảm prompt, xử lý bảng cực lớn; sau đó **program-aided solver** sinh SQL/Python trên schema+cell đã truy hồi.
- **TableRAG 2025 (arXiv:2506.10380):** tài liệu hỗn hợp text+table → giải **theo SQL vượt trội** so với xấp xỉ bằng document.
- **Pattern BRAVO:** parse bảng giữ cấu trúc + gắn **provenance (file/trang/ô) ngay lúc parse**; **nạp bảng vào DuckDB/SQLite** (query được, không flatten); schema+cell retrieval cho bảng lớn.
- ⚠️ **Provenance số trang/ô KHÔNG có giải pháp chuẩn** (RAG literature: provenance là bài toán mở) → **BRAVO phải tự build**.

## 4. Grounding + Abstention (cơ chế từ chối)
- 🔴 **Abstention CHƯA giải được ở tầng model** (AbstentionBench arXiv:2506.09038): scale model gần như vô ích; **reasoning fine-tuning làm GIẢM abstention 24%** (model suy luận "bịa context thiếu" rồi trả lời dứt khoát). → **Đừng dựa vào model tự biết dừng** — phải làm gate ở **tầng hệ thống**.
- **Vì sao finance cần abstain:** "chi phí trả lời sai >> chi phí không trả lời". Lưu ý: **uncertainty ≠ correctness**.
- **Faithfulness = traceability:** mỗi claim phải align ngược về context. SABER (4 ô: trust PK/CK/both/abstain) Pareto-dominate abstainer dựa prompt. Trust-Align: 26/27 model vượt baseline.
- **Pattern BRAVO:** (1) mọi số có provenance (metric def / ô nguồn) — không trace được thì không phát; (2) **abstain gate có ngưỡng** (ngoài metric layer + retrieval kém → từ chối/hỏi lại); (3) **verify hậu kiểm** đối chiếu từng số với output engine trước khi trả; (4) risk-coverage tunable kiểu SABER.

## 5. NL2SQL tự do — KHÓA khỏi số liệu tài chính
- Enterprise text-to-SQL SOTA chỉ **~36% EX** trên Spider 2.0 (ReFoRCE; o1-preview chỉ 21.3%) → **chưa đủ tin cho finance**.
- Lỗi chủ yếu là **ngữ nghĩa/ý định** (95–99% đúng cú pháp nhưng sai logic — SQL-of-Thought) → execution feedback đơn thuần không đủ.
- Nếu BRAVO giữ nhánh SQL (câu hỏi ngoài metric): bắt buộc schema-linking (retrieval+graph) + execution-guided validation + self-correction theo ngữ nghĩa + **refusal gate** (thà từ chối hơn bịa). *Nhưng số liệu tài chính KHÔNG đặt lên nhánh này.*

## 6. 🏗️ Kiến trúc tầng số liệu đề xuất (cho ARCHITECTURE.md)
```
Câu hỏi NL → [Router/Planner LLM — chỉ CHỌN] phân loại:
  (A) câu hỏi metric  → SEMANTIC/METRIC LAYER (Cube/MetricFlow) → SQL deterministic, fan-out-safe, EXPLAIN-validate
  (B) câu hỏi trên bảng tài liệu → TABLE-RAG (parse giữ cấu trúc + provenance → DuckDB → schema+cell retrieval → giải SQL)
  (C) ngoài phạm vi → ABSTAIN / hỏi lại
        ↓ (phép phái sinh)
  [CALC LAYER — sandbox không quyền ghi] PoT/PAL; số cuối từ interpreter, KHÔNG từ LLM
        ↓
  [GROUNDING & VERIFY GATE] mọi số gắn provenance · đối chiếu output engine · confidence<ngưỡng → mask/abstain
        ↓
  Trả lời + trích dẫn nguồn (tới metric def / ô nguồn)
```

## 7. Khuyến nghị công cụ cho BRAVO (từ track này)
- **Semantic layer:** Cube (ưu tiên — MCP + embedded + đã dùng cho finance) hoặc dbt MetricFlow.
- **Table store cho RAG:** DuckDB (query bảng đã parse).
- **Calc:** PoT/PAL trong sandbox (đã có tiền lệ trong letta tool_executor → chuyển thể).
- **Abstain/verify:** tự build ở tầng hệ thống (không có sẵn).

## 8. KXM / cần kiểm thêm
- Số arXiv chính xác của Ent-SQL-Bench (chỉ qua trích dẫn search).
- Accuracy tuyệt đối TableRAG NeurIPS (nằm trong full paper).
- Benchmark vendor (dbt/Cube) là điều kiện tự công bố — chỉ dấu xu hướng, không peer-reviewed.

---
*2 nghiên cứu còn lại đang chạy: LLM/embedding/OCR tiếng Việt; permission-aware RAG + rerank/hybrid + memory/HITL + eval stack. Sẽ thành findings I & J.*
