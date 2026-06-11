# MONEY-SPOTS — Các "chỗ ăn tiền" của BRAVO AI Copilot (deep research + gap analysis)

> **Nguồn:** deep-research harness (108 agent, 26 nguồn fetch, **117 claim → 25 kiểm chứng đối kháng 3-phiếu → 17 xác nhận → 8 sau tổng hợp**, 8 claim bị bác). Chạy 2026-06-11. **Chưa code** — đây là báo cáo định hướng value-capture.
> ⚠️ **ĐỌC TRƯỚC:** các con số ROI mạnh nhất đều **thiên lệch vendor** (HighRadius/IOFM-do-SAP-Concur-tài-trợ) → chỉ dùng làm **benchmark định hướng**, không phải kết quả đảm bảo. Mọi guidance định giá là của **AI cloud-native phương Tây** — chuyển sang on-prem VN **chưa nguồn nào validate**. Quy định VN biến động 2025-2026 (kiểm lại trước khi đưa vào tài liệu bán). **Mọi ROI cho bravo = "kỳ vọng cần chứng minh qua pilot", KHÔNG phải "đã đạt"** (bravo chưa có ERP data thật, chưa LLM local thật, chưa pilot).

---

## 1. Thông điệp cốt lõi (đã kiểm chứng)

1. **$ rõ nhất nằm ở automation luồng AP/AR** (xử lý hoá đơn đầu vào + đối soát công nợ) — nơi có benchmark tiền tệ: AI thu hồi công nợ giảm **DSO ~15-25 ngày** (HighRadius: 80→58, ~27%); xử lý hoá đơn thủ công tốn **~4x** so với tự động (IOFM/APQC ~3-4x). *[medium — vendor-biased; tỉ lệ đáng tin, con số tuyệt đối/hoá đơn không robust]* → **bravo THIẾU HẲN → BỔ SUNG ưu tiên #1.**
2. **Đặc thù kế-toán-thuế VN = "money spot" bản địa AI ngoại không làm được** *[high]*: **TT99/2025** (hệ tài khoản mới, hiệu lực 1/1/2026, thay TT200 — rename TK112/242, bỏ TK417/441/461/466/611/631, thêm TK332/2414/2295) + **NĐ70/2025** (hoá đơn điện tử bắt buộc, DN >1 tỷ/năm) → di trú TK + cross-check hoá đơn-tờ khai. → **bravo THIẾU → BỔ SUNG (đây là moat).**
3. **On-prem/chủ quyền = command được PREMIUM** *[high]*: **NĐ356/2025 + Luật BVDLCN 91/2025** (hiệu lực 1/1/2026) đặt nghĩa vụ đánh giá tác động **chuyển dữ liệu xuyên biên giới** (hồ sơ 60 ngày). On-prem **né** lớp này — ngân hàng/chứng khoán/bảo hiểm trả thêm. → **bravo YẾU ("sovereignty ảo" vì chưa có LLM local) → TĂNG CƯỜNG.**
4. **Agentic "đóng vòng lặp" có pricing power CAO HƠN HẲN copilot chỉ tư vấn** *[high]*: *"soft ROI giết willingness-to-pay"*; outcome-pricing (Intercom Fin $0.99/ticket-giải-quyết) bán được giá cứng. → **bravo thiên chat tra cứu (soft ROI), NHƯNG đã CÓ draft+maker-checker (close-the-loop) → GIỮ + đẩy mạnh; chat thuần khó bán giá cao một mình.**
5. **Định giá thắng = HYBRID** *[high]*: subscription nền tảng (dự đoán) + usage/outcome credits (bắt upside); SAP dùng freemium "AI Units" (Base miễn phí / Premium tính credits); GitHub chuyển per-seat → token-metering vì inference agentic đắt. **Biên AI-app chỉ 50-60%** (vs SaaS 80-90%) — **nhưng on-prem bravo dịch inference cost sang CapEx phần cứng KHÁCH → biên bravo có thể CAO HƠN** peers cloud-API (đổi lại chi phí triển khai/support per-site).

---

## 2. Bảng XẾP HẠNG "chỗ ăn tiền"

| # | Chỗ ăn tiền | $ chứng minh? | bravo | Đối thủ có? | Ưu tiên |
|---|---|---|---|---|---|
| 1 | **AP automation hoá đơn đầu vào → định khoản nháp** | ✅ mạnh (medium-conf) | ❌ **thiếu** | HighRadius·Vic.ai·SAP·(MISA?) | 🔥 **#1** |
| 2 | **Đối soát (reconciliation) NH–công nợ** | ✅ (cùng cụm AP/AR) | ❌ **thiếu** | HighRadius | 🔥 **#1** |
| 3 | **VN-native: di trú TT99 + cross-check hoá đơn-tờ khai NĐ70** | ⚠️ moat (high reg, $ suy luận) | ❌ **thiếu** | ❌ **ngoại KHÔNG** | 🔥 **#1 (moat)** |
| 4 | **Draft chứng từ/định khoản agentic (close-the-loop)** | ✅ pricing power cao | ✅ **CÓ** (draft+maker-checker) | ít vendor có HITL chuẩn | ⭐ **#2 (giữ+surface)** |
| 5 | **On-prem/sovereignty cho ngành regulated** | ✅ premium (high) | ⚠️ **yếu** (LLM local ảo) | ❌ MISA/SAP cloud-only | ⭐ **#2 (tăng cường)** |
| 6 | **Hỏi-đáp số liệu NL (analytics)** | ⚠️ soft nếu chỉ tư vấn | ✅ CÓ (mock) | MISA AVA·SAP Joule | ⭐ **#2-3 (bundle agentic)** |
| 7 | **Anomaly/fraud detection** | ❓ chưa claim $ sống | ❌ thiếu (Phase 3) | AppZen·SAP | 🔸 #3 |
| 8 | **Chat tra cứu tri thức** | ❌ **soft ROI** | ✅ **mạnh** | Glean·docsgpt | ⬇ **freemium "included", đừng bán giá cao riêng** |
| 9 | Forecasting · audit · NL exec-reporting · rút ngắn khoá sổ | ❓ chưa claim $ sống | ❌ thiếu | nhiều | 🔸 để sau (cần research $) |

> *Open question (chưa giải):* các use-case ❓ (forecasting/audit/anomaly/close) **chưa có claim ROI $ nào sống sót** kiểm chứng — cần research bổ sung benchmark $ trước khi xếp hạng đầy đủ.

---

## 3. Cơ chế value-capture (vì sao khách TRẢ TIỀN)

- **AP/reconciliation:** giờ tiết kiệm (xử lý hoá đơn ~4x rẻ hơn) + giảm sai sót + **cải thiện vòng quay tiền (DSO)**. Đo được → bán outcome.
- **VN-native (TT99/NĐ70):** **tránh phạt thuế** + tự động di trú hệ tài khoản (1/1/2026 là deadline ép buộc → nhu cầu cấp) + bắt sai lệch hoá đơn–tờ khai.
- **Agentic draft:** outcome đo được (số bút toán/draft được **duyệt-không-sửa**) → outcome-pricing.
- **On-prem:** né **nghĩa vụ + rủi ro phạt** chuyển dữ liệu xuyên biên giới (NĐ356/Luật 91) — giá trị = bảo hiểm tuân thủ cho ngành regulated.

---

## 4. Mô hình ĐỊNH GIÁ đề xuất cho bravo (VN)

> ⚠️ Chưa có dữ liệu giá thị trường VN (open question) — đây là **khung đề xuất cần khảo sát willingness-to-pay** trước khi chốt; số USD phương Tây không áp thẳng.

- **HYBRID per-site/per-module + outcome credits** (không per-query, vì on-prem):
  - **Platform fee per-site/năm** (dự đoán được, phủ triển khai+support — thay vai "2X cost-to-serve" của cloud).
  - **Module premium** bật thêm (Agent tài chính / AP-automation / Anomaly).
  - **Outcome credits** cho tác vụ đo được: *số hoá đơn xử lý*, *số draft định khoản được duyệt*, *số sai lệch hoá đơn-tờ khai phát hiện*.
- **Freemium kiểu SAP** (bắt chước Base/Premium): **chat tra cứu cơ bản "included"** (soft ROI → đừng tính giá cao riêng, dùng làm mồi); **agent tài chính/AP/anomaly = trả tiền**.
- **Đòn bẩy biên:** on-prem → inference sang CapEx khách → **biên bravo có thể > 50-60% của peers cloud-API**; bán **per-site/per-module** thay per-query. (Đổi lại: phải định cỡ phần cứng khách + chi phí support per-site.)
- **Định vị giá:** bán bằng **"chủ quyền + không bịa số + hiểu chế độ VN"** (ADR-0006), KHÔNG bán bằng "rẻ".

---

## 5. GAP ANALYSIS — map về kiểm kê bravo

### 🔴 BỔ SUNG (thiếu hẳn, $ rõ nhất)
1. **AP automation hoá đơn đầu vào → định khoản nháp** (tận dụng draft+maker-checker đã có làm "đuôi" close-the-loop).
2. **Reconciliation engine** (đối soát NH–công nợ).
3. **VN-native: engine di trú hệ tài khoản TT99 + cross-check hoá đơn điện tử (NĐ70) ↔ tờ khai** — moat.
4. **Anomaly detection** (Phase 3, blueprint AuditCopilot: ML tính điểm + LLM diễn giải).

### 🟠 TĂNG CƯỜNG (yếu/chưa chứng minh)
- **LLM local thật** (Ollama/vLLM) → để on-prem/sovereignty **hết ảo** = điều kiện bán premium tuân thủ (finding #3).
- **ERP data thật** (chờ API) — không có thì mọi ROI số liệu là kỳ vọng.
- **Product UI shell** — surface giá trị agentic (xem PRODUCT-SURFACE.md), nếu không value vô hình.

### 🟡 SỬA (định vị/giả định lệch)
- **Đừng định giá cao "chat tra cứu" một mình** (soft ROI giết WTP) → bundle/freemium, làm mồi cho module agentic.
- **Đừng kế thừa mù biên 50-60%** → on-prem có thể cao hơn nhưng phải bán per-site/per-module, không per-query.
- **Đừng phóng đại "kế-toán-VN-bẩm-sinh"** thành đã-có — hiện mới là **khẩu hiệu**; phải hiện thực bằng engine TT99/NĐ70 thật (#3 trên).

### 🟢 GIỮ (lợi thế thật, pricing power)
- **Draft queue + maker-checker** = cấu trúc agentic "đóng vòng lặp" có **pricing power cao** (finding #4) — bravo đã có sẵn, đối thủ ít có HITL chuẩn.
- **Verify-gate (không bịa số)** = bán được **niềm tin** (điều kiện CFO dám dùng).
- **RLS-in-SQL** = nền compliance dữ liệu (PDPD) — hỗ trợ định vị on-prem.

---

## 6. 2–3 use-case "ĐINH" để demo bán + metric ROI

1. **🔥 AP: hoá đơn đầu vào → định khoản nháp chờ duyệt** *(agentic close-the-loop — tận dụng draft+maker-checker đã có)*
   - **Metric ROI:** số hoá đơn/giờ; **% nháp duyệt-không-sửa**; giảm $/hoá đơn (benchmark ~4x); giảm sai sót.
   - **Vì sao đinh:** $ rõ nhất + bravo đã có "đuôi" HITL → chỉ cần thêm "đầu" trích xuất hoá đơn.
2. **🛡️ VN-native: di trú TT99 + cross-check hoá đơn–tờ khai** *(moat ngoại không có, deadline 1/1/2026 ép cầu)*
   - **Metric ROI:** số TK map tự động; số sai lệch hoá đơn–tờ khai bắt được; **tránh phạt thuế**.
3. **🔒 On-prem sovereignty cho ngành regulated** *(chứng khoán/ngân hàng)*
   - **Metric ROI:** né nghĩa vụ CDTIA (NĐ356); **0 egress** dữ liệu nhạy. ⚠️ **Cần LLM local thật trước** (hiện chưa) — nếu không, demo này là lời hứa.

---

## 7. Cảnh báo trung thực (độ tin cậy & khoảng trống)

- **ROI vendor-biased:** HighRadius/IOFM là best-case/self-reported/sponsored → chỉ benchmark định hướng; con số $/hoá đơn không robust (dải $12-40), chỉ **tỉ lệ** đáng tin.
- **Định giá phương Tây ≠ VN on-prem:** toàn bộ BVP/SAP/GitHub là cloud-native — chưa nguồn nào validate cho on-prem/air-gapped VN; cấu trúc chi phí khác cơ bản.
- **Khoảng trống lớn (open questions):** (1) **giá thị trường VN/willingness-to-pay** — KHÔNG có nguồn (cần khảo sát sơ cấp); (2) **MISA đóng gói/tính tiền AI** — cả 3 claim **bị bác 0-3** (đối thủ nội sát sườn nhất vẫn là ẩn số); (3) cơ chế **pilot-fail**; (4) ROI $ cho forecasting/audit/anomaly/close **chưa có claim sống**.
- **Quy định biến động 2025-2026:** TT99 (1/1/2026), NĐ356 (1/1/2026), NĐ70 (1/6/2025), SAP AI Units & GitHub billing (2026) — **kiểm lại trước khi đưa vào sales**.
- **Claim chỉ là suy luận (chưa verify):** *"VN-native AI tự động được mà ngoại không"* + *"on-prem cải thiện biên bravo"* — hợp lý nhưng **chưa có dữ liệu thực**; gắn nhãn kỳ-vọng.
- **bravo:** mọi ROI ở trên là **kỳ vọng phải chứng minh qua pilot** — chưa ERP data thật, chưa LLM local thật, chưa user.

---

## Nguồn chính (verified)
- AP/AR ROI: Nucleus Research (HighRadius DSO), NetSuite/IOFM (AP 4x), Vic.ai, Coupa, ChatFin.
- Định giá: **BVP Atlas AI Pricing Playbook** (hybrid, 2X+outcome, soft-ROI, biên 50-60%), SAP AI pricing (AI Units), GitHub blog (token billing), Monetizely, SaaStr.
- On-prem/compliance: Vietnam-Briefing (NĐ356), McKinsey (sovereign AI), TrueFoundry/Abacus (air-gapped regulated).
- VN kế toán/thuế: thuvienphapluat (TT99), meinvoice (NĐ70), MISA AMIS (TT99 phần mềm), dailythuetrongdat (giải trình chênh lệch hoá đơn).
- *(Bị bác 0-3: MISA modular pricing & AMIS OneAI bundling; AppZen Takeda hours; per-invoice 45→5 phút; TT99 71/113 accounts.)*

> Danh sách 26 nguồn đầy đủ trong transcript run `wf_ee3b6a66-651`.
