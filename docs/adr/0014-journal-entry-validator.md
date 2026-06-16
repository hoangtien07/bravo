# ADR-0014 — Journal-entry validator: Nợ=Có là invariant cứng (deterministic)

- **Trạng thái:** Accepted
- **Ngày:** 2026-06-15
- **Liên quan:** ADR-0004 (LLM không tính số), ADR-0012 (verify-gate), invariant #2 (write→draft),
  #3 (zero-hallucination số). Use-case A/C trong [MONEY-ENGINE-AP-TAX.md](../MONEY-ENGINE-AP-TAX.md).

## Bối cảnh

Money-engine AP sinh **bút toán nháp** từ hoá đơn điện tử. Một bút toán kế toán sai cân
(Σ Nợ ≠ Σ Có) là lỗi nghiệp vụ nghiêm trọng — không được phép lọt vào hàng đợi duyệt.
Draft.payload trước đây là JSONB tự do, không ràng buộc schema (gap deep-dive). Cần một
"artifact verifier" tất định cho hồ sơ có cấu trúc (giống handover-gate của Atlas), đặt
GIỮA map-TK và create_draft.

## Quyết định

1. **`JournalEntryPayload` (Pydantic)** là schema CHẶT cho `Draft.payload` khi
   `kind="journal_entry"` (mỗi dòng: account · debit · credit · memo · source_ref).
2. **Cân Nợ=Có là invariant CỨNG, kiểm DETERMINISTIC** (Decimal, dung sai 0 đồng, dùng
   `app/data_layer/money.py`): `@model_validator` raise nếu Σ Nợ ≠ Σ Có, hoặc một dòng
   vừa Nợ vừa Có. Bút toán lệch ⇒ KHÔNG tạo được payload ⇒ không vào draft.
3. **Cân-bằng-by-construction:** builder đặt Có 331 = Σ Nợ (chi phí + VAT) ⇒ luôn cân.
   Nếu Σ này lệch *tổng thanh toán hoá đơn* ⇒ ghi CỜ `validation_flags` + `needs_review`
   (kế toán xử ở HITL) — KHÔNG vỡ luồng.
4. **Số từ hoá đơn/calc, KHÔNG do LLM** (invariant #3): mọi số trên bút toán là Decimal
   lấy từ XML hoặc tổng-deterministic; lưu `engine_values` để verify-gate (loop) đối chiếu.
5. **Tài khoản phải hợp lệ TT99 + postable** (`CoaCatalog.is_valid_posting_account`);
   TK lạ/đã-bỏ ⇒ cờ + needs_review.

## Hệ quả

- (+) Không bút toán lệch nào lọt qua; CI có thể gate "Nợ=Có 100%".
- (+) Draft.payload có schema kiểm-chứng-được ⇒ nền cho UI review + audit + đẩy ERP sau.
- (+) Tái dùng `money.reconcile` (vốn là code chết) đúng mục đích.
- (−) Builder ý kiến rule-first có thể map sai TK ⇒ cờ needs_review, KHÔNG tự duyệt
  (maker-checker). Rule map cần KẾ TOÁN BRAVO ký nhận trước khi dùng thật.
- (−) Cân-by-construction che lệch-tổng-hoá-đơn thành cờ thay vì lỗi cứng — chấp nhận để
  không vỡ luồng; cờ + needs_review đảm bảo người thấy.
