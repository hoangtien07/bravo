# PILOT-U2-SCOPE — Copilot AP: phạm vi, luồng, tiêu chí cổng

> Tài liệu thực thi cho pilot đóng cổng L2→L3. Quyết định: [ADR-0031](adr/0031-first-pilot-ap-vertical-gate.md).
> Mũi nhọn: [ADR-0016](adr/0016-pivot-standalone-ap-vertical.md). Bậc: [MATURITY-LADDER.md](MATURITY-LADDER.md).
> Ngày: 2026-07-20 · Trạng thái: Draft chờ chủ dự án duyệt phạm vi + phân công blocker.

## 1. Mục tiêu (một câu)

Chứng minh **2–4 kế toán AP thật** dùng Copilot AP **đều đặn trong 4 tuần** trên **hoá đơn thật của chính họ**, giảm thời gian nhập liệu đo được, **không một số sai nào lọt ra ngoài** — để lấy bằng chứng giá trị + willingness-to-pay bảo vệ ngân sách add-on.

**KHÔNG mục tiêu:** thêm loại chứng từ mới; mở U3/U4/U5; đẩy nháp về ERP; nhiều phòng ban. (Đóng băng 🧊 theo [ADR-0016:71](adr/0016-pivot-standalone-ap-vertical.md#L71).)

## 2. Use case & phân loại

**U2 = Copilot AP** — bài toán **agent-write** (tool tất định + maker-checker), chạy E2E trên data thật, KHÔNG chờ ERP API. Đây là use case *thật sự cần agent* (khác U1 hỏi-đáp tri thức = RAG thuần, chạy kèm như tiện ích nền không-KPI).

## 3. Luồng chi tiết (happy path + failure + điểm kiểm soát)

```
[Kế toán] Upload hoá đơn XML  →  POST /api/invoices/draft  (quyền draft:create)
   │
   ├─ Parse tất định (defusedxml, XXE-safe)         app/ingestion/invoice_parser.py
   │     └─ FAIL: XML lỗi/thiếu field trọng yếu → 400 "không xử lý được" (không tạo nháp)
   │
   ├─ ⛔ GATE PHẠM VI (blocker chí mạng — xem §4)
   │     ├─ currency != VND            → CHẶN CỨNG (ValueError→400), chuyển HITL   [✅ đã làm]
   │     ├─ [cần làm #2] phương thức thanh toán không suy được → CỜ 331-vs-111/112
   │     ├─ [cần làm #3] giả định VAT khấu trừ → CỜ nếu ngoài phạm vi khấu trừ/SXKD
   │     └─ [cần làm #5] TK trúng crosswalk.is_removed() (TT200 đã bỏ) → CỜ needs_review
   │
   ├─ build_journal_entry (tất định)               app/accounting/journal.py
   │     ├─ Số LẤY TỪ HOÁ ĐƠN (Decimal) — LLM KHÔNG sinh (bất biến #3)
   │     ├─ Có 331 = Σ Nợ (chi phí + VAT 1331) → cân by-construction
   │     ├─ Cờ TT219 (VAT ≥20tr cần chứng từ không tiền mặt), TT45 (ngưỡng TSCĐ)
   │     └─ Number-Integrity Gate: Σ Nợ==Σ Có (dung sai 0đ) + mọi số truy về engine_values
   │           ⚠ Gate KHÔNG bảo đảm định khoản ĐÚNG NGỮ NGHĨA → việc của kế toán ở HITL
   │
   ├─ create_draft (maker-checker, RLS)            app/erp/draft_queue.py
   │     └─ Scope theo phòng người tạo · idempotent (agent_run_id, payload_hash) · audit
   │
   ▼
[Kế toán trưởng / người duyệt]  Hàng đợi duyệt nháp   (RLS theo phòng)
   ├─ Xem draft: dòng Nợ/Có + tổng + cờ validation + source_ref về dòng hoá đơn gốc
   ├─ ⛔ Anti-self-approval (không tự duyệt nháp mình tạo) · pg_advisory_xact_lock (không double-post)
   ├─ SỬA (nếu định khoản sai) → tính vào metric "phải-sửa"  |  DUYỆT → approve
   │     └─ Re-verify payload theo hash khi duyệt (chống drift)
   ▼
[Xuất] CSV/XLSX (BOM UTF-8, đúng format nhập BRAVO, có cột source_ref)   app/accounting/journal_export.py
   └─ Kế toán NHẬP TAY vào ERP  ← con người là CỔNG GHI CUỐI (non-invasive, bất biến #2)
```

**Điểm kiểm soát 4 bất biến:**
- **#1 RLS:** draft scope theo phòng người tạo; list/approve lọc ở tầng SQL; không cross-dept.
- **#2 Non-invasive:** đầu ra = file xuất để nhập tay; KHÔNG ghi ERP.
- **#3 Zero-hallucination số:** số từ hoá đơn (Decimal), engine tất định, gate cân + truy nguồn.
- **#4 Offline-capable:** luồng lõi tất định không gọi LLM → không egress; embedding bge-m3 local (xem blocker #11).

**Ranh giới egress (blocker #4):** pilot **CHỈ** dùng endpoint tất định `/api/invoices/draft`. KHÓA đường agent "giải thích định khoản" (`answer_guarded` với `money_facts`) — nó đẩy số/MST ra cloud. Agent chỉ được *giải thích draft đã có*, KHÔNG *sinh* draft số.

## 4. Phạm vi chứng từ (bắt đầu HẸP, mở dần khi metric đạt)

✅ **Nhận trong pilot:**
- Hoá đơn mua **VND**, **mua chịu** (đối ứng 331 đúng bản chất).
- **Một thuế suất** (8% hoặc 10%), DN theo **phương pháp khấu trừ**, chi phí phục vụ SXKD chịu thuế.
- Chi phí/dịch vụ vào TK rõ (627/641/642) hoặc hàng hoá thương mại (156) — nơi rule map tin cậy cao, đã kế toán duyệt.

❌ **Loại trước (chuyển HITL thủ công):**
ngoại tệ · mua trả ngay (111/112) · TSCĐ 211 (cần xác nhận thời gian sử dụng TT45) · nhiều thuế suất / chiết khấu dòng-tổng · VAT không khấu trừ (vốn hoá) · hàng nhập khẩu (thuế NK/TTĐB) · tạm ứng/trả trước · hoá đơn thiếu field trọng yếu.

## 5. Tiêu chí cổng — định nghĩa "pilot U2 thành công"

**User:** 2–4 kế toán AP thật (không được lái tay) · **Thời lượng:** 4 tuần · **Volume:** ≥100–150 hoá đơn thật.

| # | Metric | Ngưỡng PASS | Chứng minh |
|---|--------|-------------|-----------|
| 1 | STP rate (duyệt-không-sửa) | **≥ 70–85%** | Chất lượng engine đủ tin để giảm việc |
| 2 | Bút toán lệch Nợ=Có lọt gate | **0** | Bất biến #3 |
| 3 | Giảm thời gian/hoá đơn (vs nhập tay) | **≥ 40%** | ROI cứng (quy ra giờ công/tháng) |
| 4 | Rò RLS (thấy chứng từ ngoài phạm vi) | **0** | Bất biến #1 |
| 5 | Retention tuần-4 ≥ tuần-1 | **≥ 80% user active** | Không phải đồ chơi |
| 6 | Willingness-to-pay định tính | **≥ 2/4 user + 1 quản lý** "đáng trả tiền" | Tín hiệu doanh thu |
| 7 | "Silent wrong" (TK sai auto-post không cờ, kế toán không bắt) | **0** (đo qua override-rate từng rule) | Niềm tin số |

**FAIL NGAY nếu:** metric #2 > 0 **hoặc** #4 > 0 (bất biến — một lần vi phạm là fail, bất kể số còn lại).

**Cách demo bán (không demo tính năng — demo trước/sau):** "Kế toán X trước mất ~6 phút/hoá đơn, giờ ~2 phút; 150 hoá đơn/tháng = tiết kiệm Y giờ; mọi bút toán truy nguồn được về hoá đơn gốc." Định giá gợi ý: per-site/năm module AP (+ bậc theo volume), **không** per-user.

## 6. Checklist blocker trước khi mở cho user thật

**U2 — định khoản/an ninh:**
- [x] #1 Chặn cứng ngoại tệ (`journal.build_journal_entry`, test xanh).
- [ ] #2 Cờ phương thức thanh toán cho MỌI hoá đơn (331 vs 111/112).
- [ ] #3 Giới hạn/cờ DN khấu trừ + chi phí SXKD (VAT không mặc nhiên Nợ 1331).
- [ ] #4 Khoá đường egress agent/guarded trong pilot (chỉ endpoint tất định).
- [ ] #5 Nối `crosswalk.is_removed()` vào gate.
- [ ] Xác nhận với đội BRAVO: COA hiện đã thuần TT99 hay còn mã TT200 cũ.

**U1 (nếu bật làm nền — corpus tri thức hỗn hợp 3 loại, xem [USECASE-INVENTORY.md §1](USECASE-INVENTORY.md)):**
- [ ] #6 Allowlist corpus + assertion pre-egress kể cả `cloud_only`. ⚠ Corpus KHÔNG chỉ là user-guide:
      còn `technical_manual` (DLL) và `kqpt_ptnv` (41% chunk-volume, phân tích nghiệp vụ nội bộ) — phải
      quyết định RÕ từng `source_type` nào được egress ra cloud (kqpt/technical nhạy hơn user-guide).
- [x] #7 Number-integrity gate trên `/api/ask` (`answer_grounded`, test xanh).
- [ ] #8 Trang trích dẫn = trang chứa câu trả lời (không phải đầu section).
- [ ] #9 actor_id trong audit egress + kiểm chứng câu↔citation.

**Vận hành (cả hai):**
- [ ] #10 Chạy restore drill (điền RTO thật vào `RUNBOOK-DR.md`) + backup off-VM (GCS, Object Versioning) + uploads durability (`docker-compose.prod.yml`).
- [ ] #11 Embedding bge-m3 local 1024-dim (tránh nợ re-ingest + giữ text không rời máy).
- [ ] #12 Cost cap per-user (gpt-4o vision) + `validate_boot()` pass + firewall chỉ 80/443.

## 7. Trạng thái hiện tại (2026-07-20)

Đã làm trong đợt này: blocker **#1** (chặn ngoại tệ) + **#7** (number-gate `/api/ask`), kèm test. Còn lại là điều kiện tiên quyết trước khi bấm nút pilot với kế toán thật.
