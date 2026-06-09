# Findings I — LLM / Embedding / OCR tiếng Việt (chốt model cục bộ)

> Lấp khoảng trống lớn nhất của Track B (tiếng Việt — quyết định model). Agent đọc VMLU/VN-MTEB/VLSP + arXiv, 2026-06-08. Phân biệt [Sự thật]/[Suy luận]/KXM.

## 0. Kết luận: GIỮ Qwen-2.5 là ĐÚNG — đã xác minh
**Qwen2.5 vượt MỌI LLM tiếng Việt chuyên biệt ở mọi cỡ** (VMLU). Không cần PhoGPT/Vistral/VBD-LLaMA cho hiểu-hỏi-đáp.

## 1. Hiệu năng tiếng Việt (VMLU leaderboard, thang 100)
| Model | Cỡ | VMLU | Ghi chú |
|---|---|---|---|
| **Qwen2.5-72B-AWQ** | 72B | **69.17** | đứng đầu bảng, trên GPT-4 (65.53) & Llama-3-70B |
| KiLM-13b (Zalo) | 13B | 66.07 | VN chuyên biệt tốt nhất |
| **Qwen2.5-7B-Instruct** | 7B | **57.51** | vượt SeaLLM 7B (53.3), Vistral 7B (50.1), **PhoGPT (24.0!)**, VBD-LLaMA (37.0) |
| Vistral-7B / PhoGPT-7B5 | 7B | 50.07 / 24.01 | thế hệ cũ, đã bị vượt |

- 14B/32B Qwen **KXM** trên leaderboard → [Suy luận] ~62–67 (ngoại suy scaling).
- *Cảnh báo:* VMLU tự cảnh báo nhiễu prompt/distillation → chỉ dấu, không tuyệt đối.

## 2. Suy luận số/tài chính tiếng Việt
- Có benchmark **VLSP 2025 ViNumQA** (FinQA tiếng Việt). **Họ Qwen thống trị** (MoFin, Qwen3-8B+GRPO đạt PA 77.87%). EA hệ tốt ~79%.
- ViNumQA đo **tính toán** (phần khó nhất). BRAVO chỉ **diễn giải, không tính** (ADR-0004) → tác vụ dễ hơn nhiều → **Qwen2.5 (7B trở lên) dư sức**. Vẫn không để LLM tự cộng trừ.

## 3. Embedding (VN-MTEB, arXiv:2507.21500)
| Model | Cỡ | Retrieval | Ghi chú |
|---|---|---|---|
| gte-Qwen2-7B-instruct | 7B | **46.05** | dẫn đầu retrieval (tốn ~7B VRAM) |
| e5-Mistral-7B-instruct | 7B | 41.73 | overall cao |
| **bge-m3** | 568M | 39.84 | **dense+sparse+ColBERT 1 model, ctx 8192** |
| halong-embedding | 278M | 34.45 | siêu nhẹ VN |
- *Lưu ý:* VN-MTEB là **dữ liệu dịch máy** → POC trên dữ liệu BRAVO thật.

## 4. OCR tiếng Việt (chứng từ scan)
- **Pattern tốt nhất: PaddleOCR/PAN (detect) → VietOCR Seq2Seq (recognize) → hậu xử lý từ điển/chính tả.** Tesseract+vie chỉ tốt với in sạch ≥300 DPI.
- 🔴 **Nhận dạng CẤU TRÚC BẢNG tài chính CHƯA giải tốt** trong open-source → **rủi ro ingest lớn nhất của BRAVO** → cần POC riêng trên mẫu chứng từ thật (cân nhắc VLM/dịch vụ cho chứng từ nhiều bảng).

## 5. Lượng tử hoá
- Q8 ≈ vô tổn thất; Q4_K_M mất ~1–3% MMLU. **Model lớn chịu nén tốt hơn:** Qwen2.5 7B mất ~6.8%, **32B chỉ ~2%**, 72B +0.7%.
- Đa ngữ bị hại nặng hơn + **benchmark tự động che giấu** (drop 1.7% auto = 16% theo người). Tiếng Việt (Latin) đỡ hơn phi-Latin nhưng vẫn rủi ro hơn tiếng Anh.
- → **Model lớn nén cao > model nhỏ FP16** (32B@Q4 > 7B@FP16). AWQ + calibration đa ngữ cho throughput cao.

## 6. 🎯 Khuyến nghị model cục bộ (→ ADR-0009)
- **LLM chính: Qwen2.5-32B-Instruct @ AWQ/Q4_K_M (~20GB VRAM).** Bậc thấp: 14B@Q5 (~10GB); 7B@Q6/Q8 (~8–12GB, không Q4 ở 7B). Bỏ PhoGPT/Vistral/VBD-LLaMA.
- **Embedding: bge-m3** (hybrid 1 model) + **reranker tiếng Việt ViRanker/PhoRanker**. Nâng cấp: gte-Qwen2-7B nếu dư VRAM.
- **OCR: PaddleOCR(detect)+VietOCR(recognize)+hậu xử lý**; **POC riêng cho bảng**.
- **Bắt buộc:** eval nội bộ tiếng Việt trên prompt tài chính thật (benchmark auto che giấu suy giảm ~10×).

## Nguồn
VMLU (vmlu.ai, ACL 2025 2025.acl-long.563) · VLSP 2025 (2025.vlsp-1.25/26/27) · VN-MTEB (arXiv:2507.21500) · BGE-M3 (2402.03216) · ViRanker (2509.09131) · OCR survey (2506.05061) · quantization (2407.03211, 2505.20276, 2601.18306).
