# 0017. Gói tính năng DEMO NỘI BỘ: Knowledge Graph + AP đầy đủ + agent trên MOCK

- **Trạng thái:** Accepted (phạm vi hẹp — chỉ cho demo nội bộ)
- **Ngày:** 2026-06-29
- **Người quyết định:** Chủ dự án (chỉ đạo trực tiếp) + rà soát kỹ thuật.
- **Liên quan:** **tạm nới** chủ trương "đóng băng agent #2–4" của [ADR-0016](0016-pivot-standalone-ap-vertical.md) (vẫn Proposed) cho mục đích demo; xây trên hạ tầng [0010](0010-agent-loop-architecture.md)/[0012](0012-verify-gate-number-integrity.md)/[0014](0014-journal-entry-validator.md); giữ 4 bất biến.

## Bối cảnh (Context)
Cần một **bản demo NỘI BỘ giàu tính năng** để đưa tới lãnh đạo có "nhiều cái để test" và thu feedback sớm. [ADR-0016] chủ trương đóng băng agent #2–4 tới khi có khách thật — đúng cho **thương mại hoá** (đừng làm bề rộng khi 0 khách). Nhưng bối cảnh ở đây là **demo nội bộ** (không phải bán), nơi bề rộng có kiểm soát giúp thu phản hồi và định hướng — mục tiêu khác, nên nới có chủ đích.

## Quyết định (Decision)
Xây **gói demo** sau, tất cả **trên DỮ LIỆU MOCK / corpus có sẵn**, KHÔNG cam kết production:
1. **Knowledge Graph** (`GET /api/graph` + FE force-graph): nodes = tài liệu RLS-scoped, edges = tương đồng centroid embedding (grounded, không LLM). Thao tác: tìm/lọc/zoom, mở file gốc, hỏi AI.
2. **AP đầy đủ**: lọc trạng thái, export gộp lô CSV, lưu+xem chi tiết hoá đơn gốc, 4 fixture show hết gate (TSCĐ/VAT/rule-miss).
3. **Anomaly agent** (`app/agent/anomaly.py` + `POST /api/agents/anomaly/scan`): engine TẤT ĐỊNH (trùng/số-tròn/ngoài-giờ) → cờ `anomaly_flag` chờ duyệt; chỉ FLAG, số từ dữ liệu.
4. **Tax agent** (khi có dictionary/mock người dùng cấp): Lớp 1 RAG tra luật (tái dùng RAG); Lớp 2 đối chiếu hoá đơn↔tờ khai → draft `tax_adjustment`.
5. **Bỏ AR-Collections**: nhắc nợ là rule tất định, không phải điểm mạnh AI (quyết định của chủ dự án).

**Ranh giới bắt buộc (giữ 4 bất biến):**
- RLS ở tầng SQL cho cả graph (chunk/source scope filter cả hai vế cạnh) lẫn agent.
- Agent chỉ tạo **draft chờ duyệt** (non-invasive); số qua verify-gate; mọi LLM qua `router.chat`.
- Cạnh graph & cờ agent **grounded** (embedding/quy tắc), LLM không phịa quan hệ/số.
- **Demo-grade trên mock**: không phải cam kết bán; ADR-0016 vẫn Proposed. Khi thương mại hoá phải đánh giá lại theo maturity-ladder + phản hồi thật.

## Hệ quả (Consequences)
- **+** Demo nội bộ nhiều tính năng để test/thu feedback; chứng minh năng lực agentic + RAG + trực quan hoá.
- **+** Tái dùng ~90% hạ tầng (draft_queue, verify-gate, RLS, semantic, cosine) — công thấp.
- **−** Tạm lệch kỷ luật "đóng băng agent"; phải ghi rõ đây là DEMO, tránh ngộ nhận "sản phẩm sẵn sàng bán".
- **−** Dữ liệu là mock/corpus nội bộ; giá trị số liệu chỉ minh hoạ (is_demo=True), chưa nối ERP thật.

## Điều kiện rút lui / nâng cấp
- Khi đi thương mại: quay lại kỷ luật [ADR-0016] (freeze cho tới ≥1 khách), giữ lại những gì có phản hồi tích cực.
- Tax agent phụ thuộc dictionary/mock người dùng cung cấp; chưa có thì chỉ chạy Lớp 1 (RAG).
