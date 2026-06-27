# AR-COLLECTIONS-AGENT — đào sâu thiết kế (agent kế tiếp sau Tax&AP)

> 🧊 **FROZEN — thiết kế, KHÔNG triển khai cho tới khi: (a) đạt L3 + ≥1 khách hàng thật, và (b) lõi AP/Tax ship được.** Đây là tài liệu kế hoạch, không phải cam kết tiến độ. Lý do đóng băng: tránh "bẫy L1" của [MATURITY-LADDER.md](MATURITY-LADDER.md) (thiết kế nhiều agent khi 0 user). Xem [ADR-0016](adr/0016-pivot-standalone-ap-vertical.md).

> Từ [research/AGENT-OPPORTUNITIES.md](research/AGENT-OPPORTUNITIES.md): **AR collections = #1 bravo-fit** (close-the-loop nhất, tái dùng draft+verify+RLS, judgment thấp). **Chưa code — thiết kế.**
> ⚠️ **ROI:** vòng research chứng minh **ROI vendor (HighRadius/Billtrust/Tesorio) KHÔNG đáng tin** — KHÔNG dùng trong sales. Giá trị bán bằng **pilot đo DSO/tiền-thu của CHÍNH khách**.
> **Triết lý:** tái dùng ~70% cái bravo ĐÃ CÓ (draft_queue + maker-checker = "đuôi" close-the-loop; verify-gate; semantic catalog; AgentRun; RLS) — chỉ xây "đầu" (aging + scoring + soạn nhắc nợ).

---

## 0. Agent làm gì (1 câu)
> Định kỳ **soi công nợ phải thu quá hạn/rủi ro → ưu tiên → soạn HÀNH ĐỘNG THU NỢ dạng NHÁP chờ kế toán duyệt** (nhắc nợ theo cấp độ + kế hoạch thu), KHÔNG tự gửi/tự xoá nợ. Outcome đo được: DSO ↓, tiền thu ↑.

## 1. Luồng (deterministic backbone + LLM-in-slot + HITL)
```
[Lịch / yêu cầu]  → AgentRun (nền, paused-for-approval — ĐÃ CÓ)
  → [DETERMINISTIC] lấy AR aging từ ERP: dư nợ theo khách × tuổi nợ (0-30/31-60/61-90/>90) × hạn thanh toán
       (semantic metric: cong_no_qua_han, cong_no_theo_khach_hang — ĐÃ CÓ trong catalog)
  → [DETERMINISTIC] scoring rủi ro/ưu tiên (rule: tuổi nợ × số tiền × lịch sử trả × hạn mức) — calc Decimal
  → [LLM-GỢI-Ý] xếp hạng + soạn nội dung nhắc nợ tiếng Việt theo CẤP ĐỘ (nhắc nhẹ → cứng) + diễn giải
       (LLM KHÔNG sinh số; số nợ/ngày từ engine)
  → [DETERMINISTIC] verify-gate: mọi số nợ/ngày-quá-hạn khớp bản ghi ERP + trích dẫn (hoá đơn/khách)
  → [HITL] mỗi hành động = draft_queue.create_draft(kind="collection_action") chờ duyệt (maker-checker)
  → [người duyệt] → (W2.3 "duyệt = thực thi": complete_on_approval — ĐÃ CÓ)
  → [SAU, có tích hợp] gửi email/SMS / ghi cam kết trả — VẪN qua duyệt
```

## 2. Tái dùng bravo (đòn bẩy — đừng xây lại)
| Thành phần | bravo ĐÃ CÓ | Cần thêm |
|---|---|---|
| Aging / metric công nợ | ✅ `cong_no_qua_han`, `cong_no_theo_khach_hang` (semantic, mock) | aging buckets (0-30/.../>90) + DataSource ERP thật |
| Số không bịa | ✅ verify-gate + calc Decimal | — |
| Hành động = nháp chờ duyệt | ✅ `draft_queue` + maker-checker (kind mới `collection_action`) | UI review nhắc nợ (PRODUCT-SURFACE PS-3) |
| Run nền + resume + "duyệt=thực thi" | ✅ AgentRun + `complete_on_approval` | **scheduler** (cron/arq) |
| RLS | ✅ theo phòng | scope **theo nhân viên phụ trách khách** |
| Soạn nội dung | ✅ Model Router (egress-audit) | template nhắc nợ theo cấp độ |
| Audit-trail | ✅ AuditLog mọi draft/duyệt | — |

## 3. Ranh giới — chỗ AI KHÔNG tự quyết (governance + quan hệ khách)
- **KHÔNG tự gửi nhắc nợ** → draft chờ duyệt (gửi nhầm khách / sai giọng = hỏng quan hệ + rủi ro pháp lý). Non-invasive.
- **KHÔNG tự quyết xoá nợ / giãn nợ / trích lập dự phòng** (judgment kế toán → người).
- **LLM không sinh số nợ**; số từ ERP/calc; verify-gate chặn.
- **RLS:** nhân viên chỉ thấy khách mình phụ trách (chống rò danh sách công nợ liên-phòng/liên-NV).
- Nội dung nhắc nợ qua **egress-audit** (router) nếu dùng cloud — dữ liệu khách là nhạy.

## 4. Metric ROI (đo của CHÍNH khách — KHÔNG dùng số vendor)
- **DSO** (days sales outstanding) trước/sau N tháng.
- **% công nợ quá hạn thu được** / tiền thu trong N ngày sau nhắc.
- số nhắc nợ/giờ · **% draft duyệt-không-sửa** (chất lượng đề xuất).
- ⚠️ Mọi con số = **đo qua pilot**, không hứa ROI vendor (đã bị bác trong research).

## 5. Demo (mock — KHÔNG cần ERP)
"Soi công nợ quá hạn (mock aging) → **top 10 khách rủi ro** kèm tuổi nợ + số tiền (verify-gate, trích dẫn) → **draft nhắc nợ cấp 1/2/3 chờ duyệt** → kế toán Review/Approve." Tận dụng draft+verify+RLS+semantic đã có → demo được sớm như use-case A của Tax&AP.

## 6. Lộ trình build (sau Tax&AP)
- **Làm NGAY với mock:** aging buckets + scoring rule + soạn nhắc nợ + `create_draft(kind="collection_action")` + verify (cắm vào draft/verify/semantic ĐÃ CÓ). Bổ sung mock công nợ vào `mock_financials_tt99.yaml`.
- **Cần ERP:** DataSource công nợ thật (aging, payment terms, lịch sử trả) + **scheduler** (arq/cron cho run nền).
- **Cần sau:** tích hợp gửi (email/SMS) — vẫn sau duyệt.

## 7. Phụ thuộc & cảnh báo trung thực
- **ERP read công nợ** (aging + payment terms + lịch sử thanh toán) — chờ API (như Tax&AP).
- **Cần kế toán BRAVO xác nhận:** quy tắc scoring rủi ro, cấp độ nhắc nợ, ngưỡng "quá hạn".
- **ROI = kỳ vọng, pilot đo** — KHÔNG trích ROI vendor (Coca-Cola/Billtrust/Tesorio đã bị bác).
- **Giữ HITL tuyệt đối** cho mọi liên hệ khách (đừng auto-send) — đây là ranh giới non-invasive + bảo vệ quan hệ khách.

---
> AR collections tái dùng đúng "đuôi" close-the-loop của bravo (draft+duyệt+verify+RLS+AgentRun) — chỉ thêm aging+scoring+soạn-nhắc-nợ. Demo được trên mock không cần ERP; bán bằng **pilot đo DSO**, không bằng ROI vendor. Cùng họ với Tax&AP engine (đều: đọc ERP → draft chờ duyệt → outcome đo được).
