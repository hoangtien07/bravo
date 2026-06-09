# Findings G — Khảo sát đối thủ còn thiếu (deep-dive)

> Lấp phần Track A bỏ sót (do rate-limit chỉ kiểm chứng sâu 4 đối thủ + MISA). 3 agent đọc nguồn gốc, chạy 2026-06-08, không dính rate-limit. Phủ ~17 đối thủ ở 3 nhóm.
> ⚠️ **Quy ước:** nhiều ô là **KXM (không xác minh được)** vì hãng **không công bố công khai** chi tiết (on-prem, RLS-SQL, citation) — *KXM ≠ "họ không có"*; cần RFP/demo để chốt.

## 1. Đối thủ VIỆT NAM

| Nhà cung cấp | On-prem/offline | LLM cục bộ/tiếng Việt | Phân tích TC/ERP | RLS/phân quyền | Trích dẫn số | Đe doạ BRAVO |
|---|---|---|---|---|---|---|
| **MISA AMIS (AVA/OneAI)** | ❌ Cloud (data ở MISA) | ◐ GenAI+NLP | ✅✅ mạnh, trên ERP kế toán | ✅ phòng ban/vai trò; RLS-SQL KXM | KXM | **🔴 CAO** |
| **FPT** (AI Factory/Agents) | ✅ có nêu on-prem/hybrid; air-gap KXM | ✅ tối ưu tiếng Việt | ◐ không nêu TC/ERP | KXM | KXM | 🟠 TB |
| **Base.vn** (FPT) | KXM (SaaS) | KXM | ◐ module tài chính+AI | ◐ phân quyền nền tảng | KXM | 🟠 TB |
| **Bizzi** | ◐ cloud (on-prem KXM) | ❌ AI bóc tách, không hội thoại | ◐ tự động hoá AP, tích hợp SAP/Oracle/D365 | KXM | ❌ | 🟡 Thấp–TB |
| **Viettel** (VT-Super-120B) | ◐ Nemotron-based; on-prem KXM | ✅✅ 120B tiếng Việt (6/2026) | ◐ pháp luật trước | KXM | KXM | 🟡 Thấp (tiềm năng cao) |
| **VNPT AI** (SmartBot/iKNOW) | KXM (data tại VN) | ✅ LLM tiếng Việt | ◐ tích hợp ERP, không phân tích TC | ✅ RBAC (iKNOW) | KXM | 🟢 Thấp |
| **VinAI/VinBigData** | ◐ PhoGPT open-source→self-host | ✅✅ PhoGPT/ViGPT | ❌ | KXM | KXM | 🟢 Thấp |
| **Zalo AI** (KiLM) | KXM (cloud) | ✅✅ KiLM | ❌ | KXM | KXM | 🟢 Thấp |
| **KiotViet** | ❌ SaaS | KXM | ◐ phân tích bán lẻ/tồn kho | KXM | KXM | 🟢 Thấp |

**Kết luận VN:** đối thủ đáng lo nhất vẫn là **MISA** (trùng chức năng + thương hiệu kế toán số 1). **FPT** & **Base.vn** đe doạ trung bình (có hạ tầng on-prem / module tài chính nhưng chưa nhắm thẳng "copilot phân tích kế toán"). **Bizzi** gần mảng tài chính nhưng là tự-động-hoá-hoá-đơn, không phải copilot hội thoại. Các hãng còn lại là **nhà cung cấp model nền/chatbot/tiêu dùng**, khác phân khúc.

> ✅ **White space VN xác nhận:** **không nhà cung cấp VN nào công bố** đủ tổ hợp *on-prem/offline + RLS-SQL phòng ban + trích dẫn nguồn chống bịa số, cho phân tích tài chính ERP tiếng Việt.* Đó là moat của BRAVO.

## 2. Enterprise RAG TOÀN CẦU

| Nền tảng | On-prem/air-gap | LLM cục bộ | Permission-aware | Trích dẫn | TC/ERP-native | Giá |
|---|---|---|---|---|---|---|
| **Glean** | ✅ on-prem qua Dell (5/2025); air-gap KXM | KXM | ✅✅ mạnh (ACL+identity) | ✅ | ❌ tổng quát | ~$45–65/user, sàn ~$50–60K (nguồn đối thủ) |
| **Writer** | ✅ self-host Palmyra + cloud riêng | ✅ (host Palmyra; OSS Small/Base) | ✅ RBAC; per-doc KXM | ◐ Knowledge Graph RAG | ◐ **PalmyraFin** (không ERP-native) | Starter $29/user; Ent custom |
| **Google Agentspace/Gemini Ent** | ✅ on-prem qua GDC | gắn Gemini; local KXM | ✅ honor source ACL | KXM | ❌ tổng quát | ~$9–45/user, min 25 |
| **Hebbia** | KXM (SaaS/Azure) | ❌ OpenAI/Anthropic | KXM | ✅✅ cell-level (92% acc) | ◐ **vertical finance/legal** (phân tích tài liệu) | ~$20K/user/năm (ước tính) |
| **Sana** (Workday) | single-tenant cloud; on-prem thật KXM | model-agnostic; local KXM | ✅ mirror SSO | ✅ | ❌ tổng quát | Freemium; Ent custom |
| **Dust** | ❌ SaaS (repo MIT nhưng không self-host được) | ❌ 4 họ cloud | ❌ **yếu** (chỉ ACL theo Space) | KXM | ❌ tổng quát | Pro €29/user |
| **ChatGPT Enterprise** | ❌ cloud-only (residency 10+ vùng) | ❌ | ✅ respect app perms, RBAC | KXM | ❌ tổng quát | ~$60/user, **min 150 seat (~$108K/năm)** |

**Đe doạ với BRAVO: THẤP–TB.** Chỉ Glean/Writer/Agentspace có on-prem thật; **không cái nào xác minh được air-gapped hoàn toàn**, **không cái nào ERP-native tài chính**, **không cái nào tiếng Việt**. Đáng cảnh giác nhất: **Glean** (thông điệp on-prem+permission+citation trưởng thành — nếu một SI Việt mang vào) và **Writer** (trùng triết lý self-host LLM + có PalmyraFin). Rủi ro chính là **tốc độ** (đối thủ nhiều tiền) chứ không phải sản phẩm hiện hữu.

## 3. AI nhúng ERP/KẾ TOÁN

| Sản phẩm | On-prem | Trích dẫn số (chống bịa) | RLS tầng AI | Nháp chờ duyệt | Tiếng Việt/VAS | Giá |
|---|---|---|---|---|---|---|
| **Zoho Zia/Books** | ❌ cloud | KXM | KXM (RBAC chung) | ◐ Transaction Approval (không riêng Zia) | ❌ | AI gộp trong gói |
| **Sage Copilot** | ❌ cloud | ◐ "trained on tax rules" (không citation) | 🔴 **lỗi isolation 1/2025** | KXM | ❌ | add-on, báo giá riêng |
| **Intuit/QuickBooks AI** | ❌ cloud | KXM | ◐ theo plan tier | ✅ review & approve | ❌ | Advanced $275/th (8/2025) |
| **Xero JAX** | ❌ cloud | ◐ **"JAX Assure"** lọc hallucination | ◐ role standard/advisor | ◐ tạo hoá đơn draft | ❌ (beta US/AU) | KXM (beta) |
| **Acumatica** | ⚠️ ERP on-prem được; **AI cloud-native** | KXM | ◐ private LLM isolation | KXM | ❌ | KXM |
| **Epicor Prism** | ⚠️ ERP cloud+on-prem; AI "chủ yếu xem" | KXM | KXM | ❌ | ❌ | KXM |
| **Infor Coleman** | ❌ CloudSuite | KXM | KXM | KXM | ❌ | KXM |

**Mẫu hình AI kế toán cloud (điểm yếu BRAVO khai thác):**
1. **100% cloud multi-tenant** — không on-prem thật.
2. **Rủi ro cô lập tenant là THẬT, đã xảy ra** — sự cố **Sage Copilot 1/2025** rò dữ liệu chéo khách hàng khi hỏi hoá đơn (Sage giảm nhẹ "sự cố nhỏ, không lộ hoá đơn"). RLS-SQL on-prem của BRAVO triệt tiêu lớp rủi ro này.
3. **Chống bịa số chưa là tiêu chuẩn** — chỉ Xero "JAX Assure" tuyên bố rõ (nhưng không phải citation từng dòng).
4. **Phụ thuộc LLM bên thứ ba** (Zoho chọn provider ngoài, Xero JAX dùng OpenAI) → dữ liệu rời môi trường khách.
5. **Không nội địa hoá VAS.**

## 4. 🆕 Phát hiện chiến lược mới: Thông tư 99/2025/TT-BTC

> **Thông tư 99/2025/TT-BTC (ban hành 27/10/2025) THAY Thông tư 200/2014 từ 1/1/2026** — cải cách chế độ kế toán DN lớn nhất từ 2003: tái cấu trúc hệ thống tài khoản (thêm TK 215 Tài sản sinh học, TK 332 Cổ tức phải trả...), phương pháp định giá mới. (Nguồn: KPMG VN 11/2025, indochinalink.com, vietanlaw.com.)

→ **Vừa là yêu cầu tuân thủ vừa là điểm bán:** BRAVO cần **roadmap Thông tư 99** — AI hiểu hệ thống tài khoản mới mà đối thủ ngoại (Zoho/Xero/QuickBooks) không có. *(Cập nhật GLOSSARY/ROADMAP: thay "Thông tư 200" → "Thông tư 99/2025 (thay TT 200 từ 2026)".)*

## 5. Điều NÊN HỌC (đưa vào thiết kế/messaging)
1. **Đóng gói RLS phòng ban thành thông điệp "AI chỉ thấy thứ bạn được phép"** (chuẩn ngành: Glean/Agentspace/ChatGPT Ent) — nhấn RLS ở **tầng SQL** mạnh hơn "đồng bộ ACL" tầng ứng dụng của họ.
2. **Biến citation thành tài sản marketing đo được** — Hebbia có benchmark "92% vs 68%". BRAVO cần **con số benchmark zero-hallucination của riêng mình** (eval tiếng Việt).
3. **Đặt tên thương hiệu cho cơ chế chống-bịa** — như Xero "JAX Assure". BRAVO nên có nhãn riêng cho "zero-hallucination + trích nguồn".
4. **Duyệt theo ngưỡng** — Zoho: hoá đơn ≥ ngưỡng cần cấp cao duyệt. BRAVO nên approval theo ngưỡng tiền/loại bút toán, không chỉ "luôn tạo nháp".
5. **Mượn messaging self-host của Writer** ("data-to-desktop, không gửi dữ liệu ra ngoài") — trùng triết lý Qwen-2.5 on-prem.
6. **Phản đề "lỗ hổng kiểu Dust/Sage"** — Dust permission per-Space thô; Sage rò chéo tenant → BRAVO: "RLS per-row, per-phòng ban; on-prem không có rủi ro cô lập tenant".
7. **Tiến tới agent HÀNH ĐỘNG trong ERP** (vượt giới hạn "Glean chỉ tìm không hành động") — nhưng giữ nguyên tắc non-invasive (tạo nháp chờ duyệt).
8. **Định lượng lợi ích** (Intuit "tiết kiệm 6 giờ/tháng", đối soát "3x nhanh") + **giá minh bạch, không min-seat khủng** (đối lập ChatGPT Ent sàn ~$108K, Glean PoC $70K).
9. **Linh hoạt triển khai như Acumatica** (đổi on-prem↔cloud không phạt) — biến on-prem thành *lựa chọn*, không phải *giới hạn* (khớp hybrid ADR-0003).

## 6. Đối thủ đáng cảnh giác nhất (xếp hạng)
1. **MISA** (🔴 cao) — trùng chức năng + thương hiệu + đang tăng tốc (OneAI). Cloud-only = điểm yếu BRAVO đánh.
2. **Glean** (🟠 TB) — on-prem + permission + citation trưởng thành; rủi ro nếu vào VN qua SI.
3. **FPT / Base.vn** (🟠 TB) — hạ tầng on-prem / module tài chính, hệ sinh thái lớn; chưa nhắm thẳng copilot kế toán.
4. **Writer** (🟡 TB-thấp) — self-host LLM + PalmyraFin; rủi ro nếu địa phương hoá tiếng Việt.

## 7. Cảnh báo độ tin cậy
- Nhiều ô **KXM vì hãng không công bố** — đừng kết luận "họ không có"; xác nhận qua RFP/demo.
- Nhiều **con số giá từ trang đối thủ** (GoSearch/Workativ/Onyx) — đánh dấu rõ, cần đối chiếu sales.
- Tuyên bố hiệu năng của hãng ("nhanh 5x", "top 1") là **marketing chưa kiểm chứng độc lập**.
- Viettel VT-Super-120B rất mới (6/2026) — độ chín ứng dụng tài chính chưa rõ.

---
*Phương pháp: 3 agent đọc nguồn gốc (trang sản phẩm/thông cáo/G2 + báo VN). ~17 đối thủ. Phân biệt rõ Sự thật/Suy luận/KXM.*
