# ANOMALY-AGENT — đào sâu thiết kế (agent #2: phát hiện bất thường/gian lận)

> 🧊 **FROZEN — thiết kế, KHÔNG triển khai cho tới khi: (a) đạt L3 + ≥1 khách hàng thật, và (b) lõi AP/Tax ship được.** Đây là tài liệu kế hoạch, không phải cam kết tiến độ. Lý do đóng băng: tránh "bẫy L1" của [MATURITY-LADDER.md](MATURITY-LADDER.md) (thiết kế nhiều agent khi 0 user). Xem [ADR-0016](adr/0016-pivot-standalone-ap-vertical.md).

> Từ [research/AGENT-OPPORTUNITIES.md](research/AGENT-OPPORTUNITIES.md): Anomaly = **#2 bravo-fit** (judgment-risk THẤP — chỉ FLAG, người quyết). **Chưa code.**
> **Blueprint (AuditCopilot, research findings/K):** **engine deterministic tính điểm + LLM diễn giải + draft cờ** — hybrid (rule+ML+LLM) giảm false-positive vs pure-rule (alert-fatigue). Tái dùng verify-gate/draft/RLS/AgentRun ĐÃ CÓ; chỉ xây scoring engine.

## 0. Agent làm gì
> Agent nền định kỳ **soi bút toán/hoá đơn/chi tiêu BẤT THƯỜNG → tạo "cờ đỏ" có dẫn chứng dạng NHÁP cho người kiểm tra.** KHÔNG tự sửa/xoá/kết luận gian lận — chỉ *"nghi bất thường"* + bằng chứng.

## 1. Loại bất thường (deterministic phát hiện)
- **Bút toán:** số tròn lớn · ngoài giờ/cuối kỳ · lệch tổng-chi tiết (cross-foot) · bút toán đảo bất thường.
- **Hoá đơn:** trùng (cùng NCC + tiền + ngày) · sai MST · **NCC rủi ro** (bỏ trốn/ngừng hoạt động — tra danh sách Tổng cục Thuế = VN-moat).
- **Chi tiêu:** vượt định mức/ngân sách · tăng đột biến theo khoản mục.
- **Công nợ/kho:** số dư âm bất thường · tồn kho lệch.

## 2. Luồng (deterministic backbone + LLM-in-slot + HITL)
```
AgentRun nền (ĐÃ CÓ) → [DETERMINISTIC] engine tính điểm bất thường:
   z-score / percentile / Isolation-Forest / rule trùng-lặp / cross-foot  (calc Decimal)
 → [LLM-GỢI-Ý] xếp hạng + GIẢI THÍCH ngữ cảnh tiếng Việt + trích dẫn bản ghi (LLM KHÔNG tính điểm/sinh số)
 → [DETERMINISTIC] verify-gate: số khớp bản ghi ERP + trích dẫn (chứng từ/bút toán)
 → [HITL] draft_queue.create_draft(kind="anomaly_flag") — cờ đỏ chờ người kiểm tra
 → [người] xác nhận / bỏ qua / chuyển kiểm soát nội bộ  (KHÔNG tự xử lý)
```

## 3. Tái dùng bravo
| Thành phần | ĐÃ CÓ | Cần thêm |
|---|---|---|
| Số không bịa | ✅ verify-gate + calc Decimal | — |
| Cờ = nháp chờ người | ✅ draft_queue (kind `anomaly_flag`) | UI danh sách cờ + bằng chứng |
| Run nền + resume | ✅ AgentRun | scheduler |
| RLS | ✅ | scope theo phòng/đơn vị |
| Metric nền | ✅ semantic catalog (`but_toan_bat_thuong`, `hoa_don_trung`, `chi_vuot_dinh_muc` — ĐÃ có khung) | **scoring engine** (z-score/percentile/duplicate) + ngưỡng |

## 4. Ranh giới — chỗ AI KHÔNG tự quyết
- **CHỈ FLAG**, người quyết → judgment-risk THẤP (đây là lý do xếp #2).
- **KHÔNG kết luận "gian lận"** (pháp lý) — chỉ *"nghi bất thường"* + bằng chứng + mức độ.
- **KHÔNG tự loại/sửa/xoá** giao dịch; LLM không tính điểm (engine tính).
- **Chống alert-fatigue:** hybrid rule+ML để false-positive thấp (AuditCopilot: pure-rule đẻ FP áp đảo).

## 5. ROI (pilot đo — không số vendor)
Số cờ HỢP LỆ phát hiện sớm · thất thoát/sai sót tránh được · **tỷ lệ false-positive thấp** (alert-fatigue) · thời gian kiểm soát nội bộ. ⚠️ ROI = pilot, không trích vendor.

## 6. Demo (mock — KHÔNG cần ERP)
Mock đã có anomalies (`hoa_don_trung`, `but_toan_so_tron` trong `mock_financials_tt99.yaml`) → engine cờ + LLM giải thích + trích dẫn → draft cờ đỏ. Demo được sớm.

## 7. Phụ thuộc & cảnh báo
- ERP read sổ/bút toán/hoá đơn (chờ API) · **API tra cứu NCC rủi ro** (Tổng cục Thuế — VN-moat).
- Kế toán BRAVO xác nhận ngưỡng/định mức.
- Giữ HITL: agent là **kiểm soát hỗ trợ**, không phải kiểm toán viên.
