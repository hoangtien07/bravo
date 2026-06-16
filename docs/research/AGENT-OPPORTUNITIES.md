# Agent kế tiếp cho BRAVO (quét rộng) — deep research + bravo-fit

> **Nguồn:** deep-research model-split (Sonnet thu thập · Opus 4.8 verify+synthesize), 85 agent, **108 claim → 18 kiểm chứng → 9 xác nhận → 1 finding tổng hợp, 9 BỊ BÁC**. Chạy 2026-06-12. **Chưa code.**
> 🔴 **PHÁT HIỆN LỚN NHẤT LÀ PHỦ ĐỊNH:** verifier đối kháng (Opus) **GIẾT 9/18 claim — gồm gần như TẤT CẢ số ROI giật tít** (Coca-Cola $13M, Konica $400K, Georgetown 76%, Billtrust "99% giảm DSO", "agentic 80% ROI", Tesorio $17K/năm). ⇒ **ROI công bố của các agent tài chính phần lớn là VENDOR-MARKETING, không sống sót kiểm chứng độc lập.** Bài học: **đừng chọn "agent kế tiếp" theo ROI công bố — chọn theo bravo-fit + pilot đo ROI của CHÍNH BẠN.**

---

## 1. Thứ tự khuyến nghị (1 finding sống — directional)
> **AR collections > Anomaly/fraud > Trợ lý thuế VN.** Bằng chứng sống sót rất mỏng (Tesorio "Cash App 95%", 1 arXiv cash-flow MAE ~$6,357). **KHÔNG có ROI-USD độc lập** — thứ tự này chủ yếu dựa **bravo-fit (phân tích dưới), không phải ROI số.**

## 2. Xếp hạng theo BRAVO-FIT (cái CÓ THỂ đánh giá — không phải ROI vapor)
> Vì ROI công bố = marketing, xếp theo 4 tiêu chí đo được: *đóng-vòng-lặp? · tái-dùng-bravo? · VN-moat? · ít-judgment-risk?*

| Ứng viên | Close-the-loop | Tái dùng bravo (draft/verify/RLS) | VN-moat | Judgment-risk | Hạng |
|---|---|---|---|---|---|
| **AR collections** (thu hồi công nợ) | ✅ (draft nhắc nợ/kế hoạch thu → duyệt) | ✅✅ cao (đọc công nợ ERP + draft + verify số) | ⚠️ TB | thấp-TB | 🥇 **#1** |
| **Anomaly/fraud** (bút toán/hoá đơn bất thường) | ✅ (draft cờ rủi ro → người) | ✅✅ cao (engine deterministic tính + LLM diễn giải + draft) | ⚠️ TB | thấp (chỉ flag, người quyết) | 🥈 **#2** |
| **Trợ lý thuế VN** (quyết toán, cross-check hoá đơn-tờ khai) | ✅ (draft kiến nghị) | ✅ (gắn Tax&AP engine) | ✅✅ **cao (ngoại không làm)** | thấp-TB | 🥉 **#3** |
| Dự báo dòng tiền | ⚠️ (tư vấn) | ⚠️ | ❌ | **cao (sai số dự báo)** | 🔸 sau |
| NL executive reporting | ❌ (soft ROI) | ✅ (đã gần có) | ❌ | TB | 🔸 bundle, đừng bán riêng |
| Spend/procurement · inventory · internal-controls | ❓ chưa rõ | ⚠️ | ⚠️ | TB | ⏳ chưa đủ dữ liệu |

## 3. Vì sao top-3 (phân tích bravo-fit — KHÔNG phải ROI công bố)
- **🥇 AR collections:** khớp nhất "đuôi" close-the-loop của bravo — đọc số dư công nợ ERP (verify-gate chống bịa) → **draft kế hoạch thu/nhắc nợ chờ duyệt** (maker-checker) → outcome đo được (tiền thu được/DSO). Tái dùng tối đa cái đã có; judgment thấp.
- **🥈 Anomaly/fraud:** đúng blueprint "deterministic tính điểm + LLM diễn giải + draft cờ" — engine tính z-score/số tròn/hoá đơn trùng/chi vượt định mức, LLM **chỉ xếp hạng + giải thích + trích dẫn**, tạo **draft cờ rủi ro** cho người (không tự quyết → judgment-risk thấp). Tái dùng verify+draft+RLS.
- **🥉 Trợ lý thuế VN:** **VN-native moat** (cross-check hoá đơn điện tử ↔ tờ khai, quyết toán) — gắn thẳng Tax&AP engine; ngoại không làm được.

## 4. GAP map về bravo
- 🟢 **GIỮ (đòn bẩy):** draft+maker-checker (close-the-loop) · verify-gate · RLS · on-prem · tích hợp ERP — cả 3 top-agent đều tái dùng.
- 🔴 **BỔ SUNG (theo thứ tự):** AR collections engine (đọc aging công nợ + draft thu) → Anomaly engine (deterministic score + LLM diễn giải) → Trợ lý thuế VN (gắn Tax&AP).
- 🟡 **SỬA định vị:** **đừng dùng ROI vendor công bố** (Coca-Cola/Billtrust/Tesorio — đã bị bác) trong tài liệu bán; thay bằng **pilot đo ROI của khách thật**. NL-reporting đừng bán riêng (soft ROI).
- ⏳ **CHƯA cam kết:** forecasting (judgment-risk cao) · spend/inventory/internal-controls (chưa đủ dữ liệu).

## 5. Cảnh báo trung thực (rất quan trọng vòng này)
- **9/18 claim BỊ BÁC** — gồm mọi con số ROI ấn tượng. **Không trích bất kỳ số ROI vendor nào vào sales** mà chưa kiểm chứng độc lập.
- **0 dữ liệu VN** (giá, willingness-to-pay, đối thủ nội) — như các vòng trước.
- **Bằng chứng sống sót mỏng** (Tesorio 95% collection, 1 arXiv MAE) → thứ tự #1-#3 là **directional + bravo-fit**, không phải kết luận-ROI. **Phải pilot để đo ROI thật.**
- Synthesis (Opus) nén quá tay (9 confirmed → 1 finding) → mục 2-3 là **phân tích bravo-fit của tôi**, không phải web-finding; phân biệt rõ.

## Nguồn (đa số blog/vendor — đã lọc qua verify)
Tesorio · HighRadius · Billtrust · AppZen · MindBridge · Planergy · Vendr · arXiv (cash-flow forecast). *(Bị bác: 9 claim ROI vendor — xem transcript `wf_4124bb95-332`.)*

---
> **Một câu:** vòng này chứng minh **ROI agent tài chính trên mạng là marketing không đáng tin** — giá trị thật là loại bỏ hype. "Agent kế tiếp" nên là **AR collections** (khớp close-the-loop nhất), rồi **Anomaly** và **Trợ lý thuế VN** — chọn theo **bravo-fit + pilot**, KHÔNG theo ROI công bố.
