# MONEY-ENGINE-ROADMAP — bản đồ "chỗ ăn tiền" của BRAVO (tổng kết 1 trang)

> Gộp toàn bộ bộ research + design: [MONEY-SPOTS](research/MONEY-SPOTS.md) · [VAS-IFRS](research/VAS-IFRS-MONEY-SPOTS.md) · [AGENT-OPPORTUNITIES](research/AGENT-OPPORTUNITIES.md) · [Tax&AP engine](MONEY-ENGINE-AP-TAX.md) · [AR](AR-COLLECTIONS-AGENT.md) · [Anomaly](ANOMALY-AGENT.md) · [Tax-assistant](TAX-ASSISTANT-AGENT.md). **Chưa code.**
>
> 🧊 **ĐÓNG BĂNG (Hội đồng 2026-06-12 · 6/6 GO_WITH_CHANGES):** Agent #1-#3 (AR · Anomaly · Trợ lý thuế) + VAS↔IFRS = **BACKLOG ĐÓNG BĂNG — KHÔNG build, KHÔNG thêm doc** cho tới khi lát cắt **AP + TT99** có **≥1 user thật** dùng. 90 ngày tới chỉ làm **3 việc** (→ §7). Hướng chiến lược ĐÚNG, nhưng đang sai altitude (5 agent design khi 0 user). **Phản biện đầy đủ: §7.**

## 1. Một câu định vị
> **BRAVO Finance AI OS** = một **engine tất định + họ AGENT "đóng vòng lặp"** trên ERP BRAVO, **on-prem · kiểm-toán-được · không bịa số · hiểu chế độ kế toán-thuế VN** — bán bằng **chủ quyền + tuân thủ + outcome đo được**, KHÔNG bằng "rẻ" hay ROI vendor.

## 2. Nền móng (ĐÃ CÓ) = đòn bẩy + MOAT cho mọi agent
`verify-gate` (không bịa số) · `draft + maker-checker` (close-the-loop HITL) · `RLS-in-SQL` · `AgentRun + complete_on_approval` · `semantic/calc Decimal` · `Model Router` (egress-audit) · `citations/audit-trail`.
> 🛡️ **MOAT (research-verified):** verify-gate + HITL + audit-trail = **ĐIỀU KIỆN để output AI tài chính kiểm-toán-được** (Big4; SR 11-7; EU AI Act 8/2026). Nhiều công cụ AI thiếu — bravo đã có sẵn.

## 3. Thứ tự "ăn tiền" (xếp theo: đã-chốt-quy-định × $ × bravo-fit × ít-judgment)
| Bậc | Sản phẩm | Vì sao | judgment | Trạng thái |
|---|---|---|---|---|
| **0** | **Tax & AP engine** (hoá đơn XML → định khoản nháp · cross-check hoá đơn-tờ khai) | hoá đơn điện tử = XML cấu trúc → trích xuất tất định, $ rõ | thấp | thiết kế xong |
| **0+** | **Tuân thủ TT99** (remap CoA cấp≥2 + sinh "Accounting Policy Regulation" + bù-trừ hợp nhất) | **quy định ĐÃ CHỐT 1/1/2026, phổ cập, cơ học** | thấp | chat-opus đang code `app/accounting/` |
| **1** | **AR collections** (aging → draft nhắc nợ chờ duyệt) | close-the-loop khớp nhất; outcome = DSO | thấp | 🧊 **ĐÓNG BĂNG** (council) |
| **2** | **Anomaly/fraud** (engine cờ + LLM diễn giải) | chỉ FLAG → judgment thấp; chống thất thoát | thấp | 🧊 **ĐÓNG BĂNG** (council) |
| **3** | **Trợ lý thuế VN** (cross-check + quyết toán + giải trình) | **VN-native moat** cao | thấp-TB | 🧊 **ĐÓNG BĂNG** (council) |
| **Sau** | **Agent VAS↔IFRS** (mapping/dual-ledger/disclosure) | thị trường hẹp, **judgment RẤT cao**, lộ trình biến động | **cao** ⚠️ | để sau, cần pilot |

> Mọi agent **dùng chung 1 khuôn**: đọc ERP (read-only) → engine tất định tính → LLM gợi ý/diễn giải (không sinh số) → verify-gate → **draft chờ duyệt** → outcome đo được. ⇒ xây thêm agent = **thêm "đầu", tái dùng "đuôi"**.

## 4. Định giá (khung — CẦN khảo sát giá VN)
- **HYBRID per-site/per-module + outcome credits** (số hoá đơn xử lý · draft duyệt · cờ hợp lệ) — KHÔNG per-query (on-prem).
- **Freemium:** chat tra cứu "included" (mồi); **agent tài chính/AP/anomaly/thuế = trả tiền**.
- **On-prem** dịch inference cost sang CapEx khách → **biên có thể > 50-60% peers cloud**.
- ⚠️ **Giá thị trường VN + willingness-to-pay = chưa có dữ liệu** (mọi vòng research đều thiếu) → **cần khảo sát sơ cấp**.

## 5. Lộ trình BUILD (bám [MATURITY-LADDER](MATURITY-LADDER.md))
1. **L1→L2 (gần nhất):** deploy demo online ([DEPLOY-DEMO](DEPLOY-DEMO.md)) + product-surface ([PRODUCT-SURFACE](PRODUCT-SURFACE.md)) + corpus thật (Docling/bge-m3). Cổng: người lạ tự dùng online.
2. **Engine bậc 0/0+:** use-case A (parser hoá đơn) + TT99 compliance (chat-opus đang làm) — demo được trên mock/hoá đơn mẫu, **không cần ERP**.
3. **Agent #1 AR collections** (mock trước) → **#2 Anomaly** → **#3 Thuế** — mỗi cái **pilot đo ROI** trước khi mở rộng.
4. **Mở khoá data thật:** khi BRAVO giao **ERP read-only API** → cắm DataSource thật (engine ERP-agnostic, đổi 1 lớp).
5. **Sàn chủ quyền thật:** Qwen local (Ollama/vLLM) → moat on-prem hết "ảo" + đo pass^k.

## 6. Cảnh báo trung thực (xuyên suốt 3 vòng research)
- **ROI agent tài chính công bố = vendor-marketing, không sống sót kiểm chứng** (9 claim bị bác) → **đừng trích vào sales; đo bằng pilot.**
- **0 dữ liệu giá/đối thủ VN** ở mọi vòng → cần **khảo sát sơ cấp**.
- **Phụ thuộc cứng:** ERP read-only API chưa có (chặn data thật) · Qwen local chưa chạy (sovereignty còn "ảo") · pilot/user thật = 0.
- **Ranh giới bất biến:** AI **không tự quyết** fair value/impairment/xử-lý-thuế-phức-tạp/xoá-nợ; **không tự gửi/nộp/ghi**; chỉ draft chờ duyệt. Mọi ROI = **kỳ vọng phải chứng minh qua pilot**.

---

## 7. PHẢN BIỆN HỘI ĐỒNG (2026-06-12) — 6 lăng kính, **6/6 GO_WITH_CHANGES**

> **Đọc đúng tinh thần:** 6/6 đồng thuận **KHÔNG** = "làm tiếp như đang làm". Nó = **"hướng ĐÚNG — hãy DỪNG làm đẹp danh mục agent trên giấy, CO LẠI một mũi nhọn để lấy bằng chứng khách thật."** Không ai phủ quyết NO_GO; cũng không ai cho GO thẳng. Mỗi phủ-quyết-viên (security · accounting · vc-skeptic) nộp ≥3 critical là **điều-kiện-chặn cứng**.

### 7.1 Bảng phán quyết
| Lăng kính | Verdict | Một câu |
|---|---|---|
| **product-strategist** | GO_WITH_CHANGES | Tư duy money-engine đúng nhưng **đang VI PHẠM chính kỷ luật MATURITY-LADDER tự đặt**: 5 agent design khi 0 user → đóng băng, dồn vào MỘT lát cắt AP+TT99 chạm user thật. |
| **vc-skeptic / GTM** | GO_WITH_CHANGES | Vẫn là **bộ tài liệu bán cho chính mình**: 0 LOI, 0 phỏng vấn CFO, willingness-to-pay 100% giả định → cắt về MỘT cửa TT99, đổi 6 tháng lấy 1 chữ ký + 10 hoá đơn thật. |
| **erp-accounting-expert** | GO_WITH_CHANGES | Hướng đúng nhưng **code đã ship có lỗi định khoản nặng** (TSCĐ map theo tên, VAT 1331 vô điều kiện, "cân Nợ=Có" là tautology) → sửa nghiệp vụ TRƯỚC khi demo cho kế toán. |
| **onprem-deployment-engineer** | GO_WITH_CHANGES | **Moat chủ quyền CHƯA tồn tại dạng vận hành**: Qwen local chưa chạy lần nào, không sizing phần cứng, không scheduler, không installer air-gapped → biên cao là giả định chưa trừ cost-to-serve. |
| **security-rls-auditor** | GO_WITH_CHANGES | Governance là moat thật nhưng còn khẩu hiệu: **RLS agent nền chưa giải · demo cloud + data thật vi phạm Luật 91 · AR auto-contact thiếu cơ sở PDPD** — 3 quả mìn chưa gỡ. |
| **rag-architect** | GO_WITH_CHANGES | **verify-gate chỉ canh SỐ, không canh tính-đúng của trích dẫn/diễn giải luật**; corpus luật-thuế chưa nạp (0 chunk) → "Trợ lý thuế = đã mạnh" là tuyên bố chưa có cơ sở. |

### 7.2 Đồng thuận
**ĐÚNG (giữ — đây là tài sản hiếm):**
- Neo chiến lược vào **TT99** (deadline pháp lý 1/1/2026, đã chốt, phổ cập, ít-judgment) = use-case DUY NHẤT có **"compelling event" / cầu-cưỡng-bức-mua**. 6/6 xác nhận.
- **Hoá đơn điện tử VN = XML có cấu trúc** (NĐ123/TT78/NĐ70) → parse deterministic, **không cần OCR đắt, không cần GPU**, demo được không cần ERP API. Lợi thế kỹ thuật THẬT. 5/6.
- Kiến trúc *"số từ XML/calc, LLM chỉ gợi-ý/diễn-giải, verify-gate chặn bịa số"* + *"thêm đầu, tái dùng đuôi"* = khung kinh tế-kỹ thuật đúng.
- **Liêm chính trí tuệ** (tự bác 9/18 ROI vendor · tự khai 0 user/0 pilot/sovereignty-ảo) = điểm mạnh hiếm, đáng tin. **Đừng phá hỏng bằng over-scope.**
- Định vị bán **"tuân thủ + chủ quyền + kiểm-toán-được"** thay vì "rẻ" là đúng (break-even on-prem 5-9 năm tự giết bài "rẻ").

**SAI / RỦI RO (sửa):**
- Bộ docs **đang VI PHẠM chính MATURITY-LADDER**: viết design đầy đủ cho 5 agent khi ở L1, 0 user → "bẫy L1" tái diễn (4/6).
- **MỌI moat tuyên bố hiện là KHẨU HIỆU, chưa là tài sản:** sovereignty (Qwen chưa chạy) · VN-native (schema/bảng map/mẫu tờ khai chưa lấy, nguồn 100% thứ-cấp) · kiểm-toán-được (audit-trail chưa tamper-evident, chưa ai audit thật).
- **Willingness-to-pay = 100% giả định:** 0 khách nêu tên, 0 phỏng vấn, 0 LOI; pricing suy từ playbook cloud phương Tây; **MISA (đối thủ sát sườn) là điểm mù hoàn toàn** (3/3 claim bị bác).
- **Phụ thuộc cứng ngoài tầm kiểm soát:** ERP read-only API mà chính BRAVO (công ty mẹ) tới 6/2026 vẫn chưa cấp → chặn mọi use-case $-rõ; Qwen local chưa boot.

### 7.3 Critical (điều-kiện-chặn cứng)
1. **Willingness-to-pay = 100% giả định** — rủi ro chết người #1: sản phẩm có thể đúng kỹ thuật/compliance/moat mà vẫn phá sản vì khách không trả. Mọi roadmap build = tối ưu một thứ **có thể không ai mua**. *(vc-skeptic, product-strategist)*
2. **Lỗi định khoản nặng trong code ĐÃ SHIP** — TSCĐ map theo **regex tên hàng** (phải theo **ngưỡng ≥30tr + thời gian dùng**, TT45); VAT mặc định **1331 khấu trừ VÔ ĐIỀU KIỆN** (bỏ qua ≥20tr thanh toán không-tiền-mặt · NCC bỏ trốn · mục đích SXKD). Kế toán phát hiện trong **5 phút đầu demo** → mất uy tín tức thì; khấu trừ VAT sai = nguồn truy thu/phạt #1 → **phản tác dụng đúng cái moat "tránh phạt"**. *(erp-accounting-expert)*
3. **RLS cho AGENT NỀN chưa giải — mâu thuẫn gốc invariant #1** — AR/Anomaly/cross-check quét TOÀN BỘ sổ theo lịch, nhưng RLS định nghĩa per-employee. Agent nền chạy dưới identity nào? Service-account-toàn-quyền ⇒ **RLS bị vô hiệu ngay agent đầu tiên**, draft lộ data liên-NV. *(security, onprem)*
4. **Demo cloud + data thật = vi phạm invariant #4 + Luật 91/2025** (chuyển data xuyên biên giới, phạt tới 3 tỷ / 5% doanh thu). **Bán "chủ quyền" nhưng demo vi phạm chủ quyền = tự mâu thuẫn chí mạng** — 1 câu hỏi của CFO/CIO regulated đủ giết deal. Egress fail-closed mới là thiết kế, chưa có code/test. *(security)*
5. **Moat on-prem được BÁN nhưng CHƯA bao giờ CHẠY** — khối vllm comment-out, Qwen2.5-32B-AWQ chưa load lần nào, demo chạy cloud trên máy không GPU. Không hardware sizing, không scheduler. **Bán một sàn offline chưa boot = bán lời hứa.** *(onprem)*
6. **verify-gate chỉ canh SỐ, không canh tính-đúng trích dẫn/diễn giải luật**; corpus luật-thuế chưa nạp (0 chunk). Lớp "Trợ lý thuế" phần lớn là **văn xuôi về luật** — LLM trích sai điều/khoản, diễn giải ngược ý mà gate cho qua hết. *(rag-architect)*

### 7.4 High
- **Over-scope:** 1 engine + 5 họ agent cho team nhỏ ở L1, 0 user → "money engine" phình thành "Finance AI OS vạn năng" — **mỗi trang design = chi phí cơ hội của một cuộc gọi khách hàng.**
- **Unit economics on-prem chưa tính:** cost-to-serve per-site (sizing GPU · cài · support air-gapped không-remote · cập nhật model offline · sign-off bảo mật mỗi khách) chưa trừ vào "biên >50-60%" — claim "biên cao hơn cloud" có thể **NGƯỢC** khi scale N site.
- **Outcome-pricing mâu thuẫn air-gapped:** metering "số draft/hoá đơn" thế nào mà **không telemetry rời mạng** (vi phạm sovereignty)? Không metering được ⇒ outcome-pricing sụp về flat per-site, biên/upside khác hẳn.
- **TT99 là doanh thu MỘT-LẦN**, không recurring — sau 1/1/2026 ai cần remap đã remap. **Đừng nhầm "wedge vào cửa" (đúng) với "dòng doanh thu bền" (sai)**; đường chuyển recurring (cross-check hàng tháng) lại bị chặn bởi ERP API chưa có.
- **AR auto-contact thiếu phân tích cơ sở pháp lý PDPD** (consent/hợp đồng · quyền rút lui · giới hạn tần suất chống quấy rối đòi nợ). AR là agent #1 → phải gỡ TRƯỚC pilot.

### 7.5 Cải thiện — làm ngay
1. **🧊 ĐÓNG BĂNG mọi doc/code agent mới** (AR · Anomaly · Tax · IFRS) → đã dán banner đầu file. *(đồng thuận 4/6)*
2. **Phỏng vấn 8-12 kế toán trưởng/CFO trong tệp BRAVO** (kênh sẵn, chi phí ≈0) về TT99: đang remap thế nào · đau nhất ở đâu · trả bao nhiêu/đơn vị → mục tiêu **≥3 LOI / cam kết trả tiền có điều kiện**. *Một LOI giá trị hơn 22 doc design — đáng làm hơn vòng deep-research thứ 4.*
3. **Sửa lỗi nghiệp vụ trước khi demo:** (a) bỏ map TSCĐ-theo-tên → rule **ngưỡng ≥30tr** đẩy về `needs_review`; (b) thêm lớp **điều kiện khấu trừ VAT** (≥20tr cần chứng từ không-tiền-mặt · NCC rủi ro · mục đích SXKD), VAT chỉ vào 1331 khi đủ điều kiện; (c) trình bày lại "cân Nợ=Có" là điều kiện **CẦN** (không-bịa-số), **KHÔNG** phải đảm bảo đúng định khoản. **Kế-toán BRAVO ký-duyệt `mapping_rules` + crosswalk TT200→TT99, đối chiếu VĂN BẢN GỐC TT99** (không chỉ nguồn thứ-cấp Big4).
4. **Định nghĩa + CODE identity/RLS cho agent nền TRƯỚC agent #1:** chạy "on-behalf-of" identity có scope cụ thể (hoặc fan-out per-NV), filter RLS trong SQL mọi truy vấn, draft mang đúng scope người duyệt. **Viết test rò-rỉ:** draft khách phòng A không xuất hiện ở hàng đợi NV phòng B.
5. **Dựng "Sovereignty Spike" THẬT:** thuê 1 máy GPU theo giờ → bỏ comment vllm → load Qwen2.5-32B-AWQ → chạy 5 smoke 100% local → **CẮT internet** → đo VRAM/token-s/p95/chất lượng tiếng Việt → 1 trang "on-prem evidence". **Cấm dùng từ "chủ quyền/on-prem" trong tài liệu bán cho tới khi có đường chạy 100% local demo được.**
6. **ADR cứng "pilot/demo data thật = LOCAL-ONLY tuyệt đối"** + cổng L3: tới khi Qwen local chạy + egress fail-closed test xanh, data khách thật KHÔNG chạm LLM cloud; demo cloud chỉ dùng data MOCK.
7. **Gate thứ hai cho văn-xuôi** (claim-citation entailment bằng local judge): mỗi câu khẳng định luật/thuế phải được đoạn-trích chống đỡ, nếu không thì mask/abstain. Nâng citation lên mức **trang/ô**. Nạp corpus luật-thuế THẬT tối thiểu (TT99 + NĐ123/TT78 + mẫu tờ khai) trước khi demo Tax-Assistant.
8. **Đối xử ERP read-only API như internal deal phải CLOSE:** deadline cứng (vd 8 tuần) + **một người BRAVO chịu trách nhiệm có tên**. Quá hạn → pivot chính thức sang use-case chỉ chạy data UPLOAD. Coi bảng map TT200→TT99 + danh sách NCC rủi ro là **ARTIFACT có nguồn-trích + version + kế-toán ký-duyệt**, không phải hằng-số code. *(verify-gate bắt số-bịa nhưng KHÔNG bắt map-sai-có-hệ-thống: số khớp, đích sai → provenance ở tầng map là chốt chặn duy nhất.)*

### 7.6 Blocking (chặn MỌI thứ NGOÀI lát cắt cốt lõi)
- ≥3 tín hiệu cầu cụ thể (**LOI / cam kết trả tiền có điều kiện cho TT99, khách BRAVO nêu tên**) TRƯỚC khi đầu tư thêm công sức build.
- Sửa lỗi map TSCĐ-bằng-tên + điều kiện khấu trừ VAT + **kế-toán BRAVO DUYỆT** mapping_rules/crosswalk (đối chiếu VĂN BẢN GỐC TT99) TRƯỚC khi dùng AP làm demo bán.
- Thiết kế + **test rò-rỉ** RLS agent nền TRƯỚC khi code AR/Anomaly.
- Ranh giới cứng **"data thật = local-only"** (ADR + cổng L3) + phân tích PDPD cho AR auto-contact TRƯỚC mọi pilot chạm data khách thật.
- **Sovereignty Spike** (≥1 lần chạy 5 smoke 100% local, internet cắt, có số đo) + **Hardware Sizing Sheet** (≥2 tier) TRƯỚC khi đưa "on-prem/chủ quyền" vào tài liệu bán hay cam kết giá per-site.
- Không dùng "lớp tra-cứu luật-thuế = đã mạnh" trong bán/demo tới khi: (a) corpus luật-thuế thật nạp với citation mức điều/khoản/trang, và (b) gate entailment cho prose.

### 7.7 Xung đột + đánh đổi
- **Mô hình thu tiền — outcome-pricing vs sovereignty air-gapped:** không metering được trên air-gapped mà không phá sovereignty. → **Đánh đổi:** dùng **flat per-site cho pilot đầu** (đơn giản, gỡ mâu thuẫn ngay, bỏ upside outcome) → chứng minh giá trị trước → thiết kế metering-ký-số-offline sau.
- **Data demo — mock vs thật:** security đẩy "data thật = local-only, demo dùng MOCK"; product/accounting nhấn "giá trị chỉ rõ khi chạy data THẬT". → **HOÀ GIẢI:** AP+TT99 trên **file upload là data thật NHƯNG không cần LLM cloud** (parse XML deterministic chạy CPU, prose ít) — *chính lý do cả 6 hội tụ về lát cắt này: vừa thật vừa local-an-toàn.*
- **Mức độ MISA:** vc-skeptic coi **Critical** (MISA có thể tung module TT99 nhanh+rẻ vì đã ở trong workflow khách → on-prem chỉ là ngách regulated hẹp); product coi High. → **Đánh đổi:** cần **định-cỡ-TAM-trung-thực**, chấp nhận thị trường mục tiêu = ngách regulated cao cấp, không đại trà.
- **TT99 là wedge hay engine:** dùng làm **wedge-vào-cửa** đúng (6/6), NHƯNG phải có đường chuyển recurring (cross-check hoá-đơn↔tờ-khai hàng tháng) — mà đường đó bị chặn bởi ERP API chưa có. **Rủi ro chiến lược trung hạn cần nhìn thẳng.**

### 7.8 🎯 CƯỢC DUY NHẤT (hội tụ 6/6)
> **AP hoá đơn điện tử XML THẬT → bút toán nháp ĐÚNG ĐỊNH KHOẢN** (TSCĐ theo ngưỡng · VAT theo điều kiện khấu trừ · map TK có **kế-toán-BRAVO-duyệt**) **chờ Review/Approve, GẮN với di trú/tuân thủ TT99** (remap CoA cấp≥2 + sinh nháp "Accounting Policy Regulation") — chạy trên **data UPLOAD/XML thật**, deploy online qua **cổng L2**, đo trên **user nội bộ BRAVO** (kế toán/helpdesk) với metric **phút/hoá-đơn + %-duyệt-không-sửa**.

**Vì sao đây là giao điểm mọi lăng kính:** (1) use-case DUY NHẤT **không bị chặn** bởi ERP API hay Qwen-local — parse XML chạy CPU, air-gapped trivially; (2) có **compelling event pháp lý ĐÃ CHỐT 1/1/2026**; (3) judgment thấp nhất → **né sạch 3 quả mìn** (egress cloud · RLS agent nền · PDPD auto-contact) mà AR/Anomaly đều dính; (4) **test thẳng lời hứa "kế-toán-VN-bẩm-sinh"** bằng %-duyệt-không-sửa — cao ⇒ moat THẬT; thấp ⇒ mọi agent sau dùng chung "đầu" map-TK này nên cùng hỏng, **phơi bày sớm**; (5) cho ra thứ cả 22 doc đang thiếu: **một con số willingness-to-pay thật**. ⚠️ TT99-migration là doanh thu **một-lần** → dùng làm wedge, đừng nhầm thành mô hình bền.

### 7.9 Kết luận trung thực — 90 ngày, **3 việc, đúng thứ tự**
1. **Phỏng vấn 8-12 CFO/kế toán trưởng tệp BRAVO → ≥3 LOI cho TT99.** Không có tín hiệu cầu thật thì mọi thứ khác là tối ưu một sản phẩm có thể không ai mua.
2. **Sửa 2 lỗi định khoản chết người** (TSCĐ-theo-tên · VAT-1331-vô-điều-kiện) + **kế-toán BRAVO ký-duyệt** bảng map đối chiếu văn-bản-gốc TT99. Kế toán phát hiện trong 5 phút đầu = mất sạch uy tín.
3. **Ship lát cắt AP+TT99 chạy LOCAL** trên hoá đơn XML thật + file CoA upload, **đo %-duyệt-không-sửa** trên user nội bộ.

→ **ĐÓNG BĂNG AR/Anomaly/Tax/IFRS** ở trạng thái design tới khi lát cắt này có **1 user thật**. Ba quả mìn (RLS agent nền · demo-cloud-Luật-91 · AR-PDPD) + moat-chưa-chạy (Sovereignty Spike · hardware sizing) là điều-kiện-chặn cho MỌI thứ NGOÀI lát cắt cốt lõi — **không phải lý do dừng lát cắt cốt lõi**, vì chính nó được thiết kế để né sạch chúng.

> **Một con số thật từ một mũi nhọn sắc trong 6 tháng đáng giá hơn năm agent thiết kế đẹp mà 0 user.**

---
> **Tinh thần (cập nhật theo Hội đồng):** một engine + nhiều agent dùng chung khuôn *"deterministic + LLM-in-slot + draft chờ duyệt"* — nhưng **CO VỀ MỘT MŨI NHỌN** (AP + TT99, data thật, local, đo trên user thật) trước khi mở thêm "đầu". Ưu tiên cái **đã-chốt-quy-định + ít-judgment + tái-dùng-nhiều**; IFRS/AR/Anomaly/Thuế **đóng băng** tới khi có 1 user thật. Thắng bằng **bằng-chứng-khách-thật (LOI → pilot → bán)**, không bằng thêm tính năng. **1 con số thật > 5 agent đẹp.**
