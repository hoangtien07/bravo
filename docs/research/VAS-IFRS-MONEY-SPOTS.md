# VAS ↔ IFRS & TT99 — chỗ ăn tiền cho BRAVO (deep research, model-split)

> **Nguồn:** deep-research harness **model-split** (Sonnet thu thập · Opus 4.8 verify+synthesize), 89 agent, **82 claim → 18 kiểm chứng đối kháng 3-phiếu → 16 xác nhận → 7 findings**, 2 bị bác. Chạy 2026-06-12. **Chưa code.**
> ⚠️ **ĐỌC TRƯỚC:** toàn bộ 16 claim là **nguồn THỨ-CẤP** (Big4 insight, advisory blog) — đủ tin để mô tả quy định, **chi tiết điều khoản phải đối chiếu văn bản gốc** (thuvienphapluat.vn) trước khi code. **Chi phí thật, giá VN, đối thủ, và toàn bộ "quét rộng" (AR/forecasting/anomaly) KHÔNG có claim nào xác minh** → coi là **giả thuyết cần pilot/khảo sát**. ROI = kỳ vọng phải chứng minh.

---

## 0. PHÁT HIỆN ĐỔI KHUNG (quan trọng nhất)
> **Money-spot gần-hạn THẬT của bravo KHÔNG phải "IFRS đầy đủ" — mà là TUÂN THỦ TT99/2025.**
- **TT99/2025** (ban hành 27/10/2025, hiệu lực **1/1/2026**, thay TT200) = bước hiện-đại-hoá-hướng-IFRS **BẮT BUỘC + gần phổ-cập** (mọi DN phạm vi TT200; **không gồm SME**). ⇒ **đã CHỐT quy định, thị trường lớn, cơ học, ít judgment** → **gộp vào "Tax & AP money engine".**
- **IFRS đầy đủ** vẫn **TỰ NGUYỆN tới hết 2025**; bắt buộc Phase II (QĐ 345) chỉ áp **BCTC hợp nhất** cho niêm yết/SOE lớn/đơn vị công lớn từ FY sau 1/1/2026 — **phạm vi hẹp + judgment-heavy + lộ trình biến động** (VFRS **chưa có timeline** tới 3/2026). ⇒ **agent tách-riêng, giai-đoạn-sau**, cần pilot.

---

## 1. Bảng cơ hội ăn tiền (xếp hạng)
| # | Cơ hội | $/cầu | bravo | judgment | Ưu tiên |
|---|---|---|---|---|---|
| 1 | **TT99: remap hệ tài khoản (CoA cấp ≥2) + sinh "Accounting Policy Regulation" bắt buộc** | ✅ đã chốt, phổ cập | ⚠️ thiếu (mở rộng Tax&AP) | **thấp (cơ học)** | 🔥 **#1 — GỘP engine** |
| 2 | **TT99: hợp nhất bắt buộc (đầu mối + đơn vị phụ thuộc, bù-trừ giao dịch nội bộ)** | ✅ đã chốt | ⚠️ thiếu | thấp-TB | 🔥 **#1 — GỘP engine** |
| 3 | **TT99: cập nhật cấu hình ERP cho FDI (SAP/Oracle/MISA) trước hạn** | ✅ cấp (deadline) | ✅ on-prem + map-TK | thấp | 🔥 **#1** |
| 4 | **Tra cứu/tuân thủ chuẩn mực liên tục (VAS/IFRS/TT99)** | ✅ phổ cập | ✅ **CÓ** (RAG có dẫn chứng) | thấp | ⭐ **#2 (đã mạnh)** |
| 5 | **VAS→IFRS mapping cơ học + gap-analysis** | ⚠️ hẹp (niêm yết/FDI) | ❌ thiếu | TB | 🔸 #3 (agent riêng, sau) |
| 6 | **Sinh nháp thuyết minh/disclosure IFRS** | ⚠️ hẹp | ❌ thiếu | TB | 🔸 #3 (có-người-duyệt) |
| 7 | **Lập BCTC IFRS đầy đủ / fair value / impairment** | ⚠️ hẹp | ❌ | **RẤT CAO** | ⛔ **AI KHÔNG tự quyết** |
| — | AR collections · forecasting · anomaly (quét rộng) | ❓ **0 claim xác minh** | ❌ | — | ⏳ cần research riêng |

## 2. Cơ chế value-capture (TT99 — money-spot #1)
- **Tác vụ LẶP LẠI, có VĂN BẢN ĐẦU RA** (Accounting Policy Regulation, bút toán bù-trừ hợp nhất, bảng map CoA) → khớp **draft + verify + RLS** của bravo.
- **DN tự sửa CoA cấp ≥2** (Level 1 cố định 71 TK) **nhưng PHẢI lập Accounting Regulation + chịu trách nhiệm pháp lý** → AI sinh **nháp** quy chế + map, **kế toán duyệt** (maker-checker). Tránh phạt + tiết kiệm giờ.
- **Hợp nhất bắt buộc** (thay "tổng hợp" cũ) → AI dựng **bút toán bù-trừ nội bộ nháp** + đối soát → ERP đa-đơn-vị.

## 3. Ranh giới AI nên / KHÔNG nên (judgment)
- ✅ **AI làm:** map CoA cơ học · sinh nháp Accounting Policy Regulation · bù-trừ hợp nhất · gap-analysis · tra cứu chuẩn mực có dẫn chứng.
- ⛔ **AI KHÔNG tự quyết:** **fair value (IFRS 13)** · **goodwill impairment (IAS 36)** · ≥12 IAS/IFRS không có VAS tương đương (IFRS 9, IAS 19/41) → **chỉ hỗ-trợ-có-người-duyệt**. *(VAS rule-based/cost-oriented vs IFRS principles-based → chuyển đổi đòi professional judgment.)*

## 4. 🛡️ Moat định-vị (rất mạnh — finding F6)
**verify-gate + maker-checker HITL + audit-trail + citations của bravo = ĐIỀU KIỆN TUÂN THỦ**, không phải tính năng tùy chọn: Big4 (Deloitte/KPMG) khẳng định output AI tài chính **phải kiểm-toán-được + có tài liệu/audit-trail** (chuẩn SR 11-7, **EU AI Act hiệu lực 8/2026**, NYDFS Part 500, DORA, NIST AI RMF). ⇒ bravo **đã có sẵn điều kiện sống còn** mà nhiều công cụ AI thiếu — **bán bằng "AI tài chính kiểm-toán-được, không bịa số"**.

## 5. KẾT LUẬN CHIẾN LƯỢC (Q7)
1. **GỘP lớp tuân-thủ-TT99 vào "Tax & AP money engine"** = play tốt nhất gần-hạn ($ × khả-thi × moat × **ít judgment-risk**; quy định đã chốt). → bổ sung: remap CoA cấp ≥2 + sinh Accounting Policy Regulation + bù-trừ hợp nhất nội bộ.
2. **TÁCH agent VAS↔IFRS riêng, giai-đoạn-sau** (mapping/dual-ledger/disclosure) cho niêm yết/FDI/vay-vốn — **judgment-heavy, có-người-duyệt, cần pilot chứng minh ROI**.
3. **KHÔNG bet vào VFRS/IFRS-mandate** (chưa timeline, phạm vi-bắt-buộc mơ hồ — 2 claim bị bác). Neo **TT99 (đã chắc)**.
4. **Quét rộng (AR/forecasting/anomaly): chưa kết luận** — đề tài này 0 claim chạm tới → **cần một vòng deep-research riêng**.

## 6. GAP map về bravo
- 🟢 **GIỮ + ĐỀ CAO:** verify-gate · maker-checker · audit-trail · citations · RLS · on-prem → **lợi thế tuân thủ** (F6).
- 🟠 **TĂNG CƯỜNG (gộp Tax&AP engine):** remap CoA cấp ≥2 · sinh Accounting Policy Regulation · bù-trừ hợp nhất nội bộ · cấu hình ERP FDI.
- 🔴 **BỔ SUNG (agent IFRS riêng, sau, có-người-duyệt):** mapping VAS→IFRS · dual-ledger · sinh nháp disclosure · gap-analysis chuẩn mực.
- ⏳ **CHƯA đủ cơ sở cam kết:** AR collections · forecasting · anomaly (cần research Q6 riêng).

## 7. Cảnh báo trung thực
- **Nguồn thứ-cấp 100%** — chưa đọc văn bản gốc TT99/QĐ345/Luật Kế toán; đối chiếu trước khi code.
- **2 claim về phạm vi-bắt-buộc IFRS bị bác** (1-2, 0-3) — kể cả "FDI bắt buộc giữ VAS + dual-report" → **"ai mua" agent IFRS CHƯA chắc**, không dùng làm cơ sở phân khúc.
- **Time-sensitive:** TT99 chắc; Circular triển-khai-IFRS riêng vẫn dự thảo; VFRS chưa timeline; mốc "bắt buộc sau 2025" từng lùi nhiều lần.
- **KHÔNG xác minh:** chi phí chuyển đổi thật · willingness-to-pay · giá/đóng gói đối thủ (Workiva/Tagetik/MISA/FAST) · **toàn bộ quét-rộng Q6** → **giả thuyết cần pilot/khảo sát.**

## Nguồn chính (verified, thứ-cấp)
KPMG VN (IFRS roadmap) · Vietnam-Briefing (Circular 99) · Indochina Link (Circular 99) · Deloitte VN (VAS→IFRS; AI finance audit-trail) · Grant Thornton · Crowe · Acclime · Expertis (khác biệt VAS-IFRS) · Duane Morris · InCorp.
*(Bị bác: 2 claim phạm-vi-bắt-buộc IFRS. Đầy đủ 27 nguồn trong transcript `wf_f9de4793-2fe`.)*
