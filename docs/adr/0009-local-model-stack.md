# 0009. Bộ model cục bộ: Qwen2.5-32B + bge-m3 + VietOCR

- **Trạng thái:** Accepted (kèm yêu cầu eval nội bộ tiếng Việt xác nhận)
- **Ngày:** 2026-06-08
- **Người quyết định:** Đội dự án BRAVO AI Copilot
- **Liên quan:** [ADR-0003](0003-hybrid-llm-strategy.md), [findings/I](../research/findings/I-vietnamese-models.md), [findings/B](../research/findings/B-academic-technical.md).

## Bối cảnh (Context)
ADR-0003 chốt hybrid (local mặc định) nhưng để mở *kích thước/model cụ thể*. Track B cảnh báo LLM nhỏ bịa số khi tính (FAITH: Qwen-3-8B 30.6%). Cần chốt model cục bộ dựa trên hiệu năng **tiếng Việt** (đã nghiên cứu — [findings/I]).

## Quyết định (Decision)
**LLM (mặc định on-prem):**
- **Chính: Qwen2.5-32B-Instruct @ AWQ/Q4_K_M (~20GB VRAM).** Lý do: Qwen2.5 đứng đầu VMLU mọi cỡ (vượt mọi LLM tiếng Việt chuyên biệt); 32B chịu quantization gần như không mất chất lượng (~2% vs 7B ~6.8%); họ Qwen thống trị benchmark tài chính-số tiếng Việt (VLSP 2025).
- **Bậc thấp:** 14B@Q5_K_M (~10GB, 1 GPU 16GB); 7B@Q6/Q8 (~8–12GB, **không Q4 ở 7B**).
- **Loại bỏ** PhoGPT/Vistral/VBD-LLaMA (thua Qwen2.5 cùng cỡ rõ rệt).
- LLM **chỉ diễn giải, không tính số** ([ADR-0004]) → 32B dư sức cho diễn giải tiếng Việt.

**Embedding:** **bge-m3** (dense+sparse+ColBERT 1 model, ctx 8192 — hợp pipeline hybrid+rerank) + **reranker tiếng Việt ViRanker/PhoRanker**. Nâng cấp tuỳ chọn: gte-Qwen2-7B-instruct (dẫn đầu VN-MTEB retrieval) nếu dư VRAM.

**OCR:** ⏸️ **TẠM DESCOPE OCR bảng tài chính scan khỏi MVP** (quyết định 2026-06-09). MVP chỉ nạp **tài liệu số (native PDF/DOCX/Excel có text)** qua Docling — không OCR. Lý do: tài liệu ERP phần lớn là số/xuất từ hệ thống; OCR cấu trúc bảng chưa giải tốt ở open-source (rủi ro cao). Khi mở lại: **PaddleOCR/PAN (detect) → VietOCR (recognize) → hậu xử lý** + POC riêng cho bảng.

**Cloud opt-in (ADR-0003):** chỉ cho dữ liệu không nhạy + khi khách bật; có thể dùng cho tác vụ suy luận cao cấp (model nhỏ open-weight yếu hơn frontier).

## Hệ quả (Consequences)
- Tích cứng: model đã được xác minh tốt nhất cho tiếng Việt; 32B@Q4 cân bằng chất lượng/VRAM; embedding hybrid hợp tài chính (sparse bắt mã chứng từ/số).
- Tiêu cực/nợ: 32B cần GPU ~20GB+ (ảnh hưởng yêu cầu phần cứng khách — `onprem-deployment-engineer` xét); khách không GPU → 7B/CPU (chất lượng thấp hơn, hoặc cloud opt-in).
- **Điều kiện bắt buộc:** **eval nội bộ tiếng Việt trên prompt tài chính thật** — benchmark tự động che giấu suy giảm đa ngữ (~10×); VMLU/VN-MTEB là chỉ dấu, không tuyệt đối.
- 🔴 **Rủi ro lớn nhất: OCR bảng** — nhận dạng cấu trúc bảng tài chính chưa giải tốt ở open-source → **POC riêng trên chứng từ thật trước khi cam kết** (cân nhắc VLM/dịch vụ).

## Tham chiếu
[findings/I](../research/findings/I-vietnamese-models.md): VMLU, VN-MTEB (2507.21500), VLSP 2025, quantization (2505.20276).
