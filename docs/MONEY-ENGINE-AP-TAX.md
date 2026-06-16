# MONEY-ENGINE-AP-TAX — Đào sâu use-case "đinh": AP hoá đơn + VN-native (TT99 + cross-check thuế)

> Gộp **2 chỗ ăn tiền hàng đầu** từ [research/MONEY-SPOTS.md](research/MONEY-SPOTS.md) — AP automation ($ rõ nhất) + moat VN-native (TT99/hoá đơn-tờ khai) — thành **MỘT sản phẩm mạch lạc** (cùng thao tác trên một bộ dữ liệu: hoá đơn điện tử, hệ tài khoản, bút toán, tờ khai). **Chưa code — thiết kế.**
> **Triết lý đào sâu:** tận dụng TỐI ĐA cái bravo ĐÃ CÓ làm **"đuôi"** (draft+maker-checker = close-the-loop có pricing power cao; verify-gate = không bịa số; calc Decimal + reconciliation; RLS; citations) — chỉ xây **"đầu"** còn thiếu (parser hoá đơn + map-TK + cross-check). Đây là cách rẻ nhất tới use-case có $ rõ.

---

## 0. Đòn bẩy CHÌA KHOÁ — hoá đơn điện tử VN là XML CÓ CẤU TRÚC
NĐ123/2020 + TT78/2021 + NĐ70/2025: hoá đơn điện tử VN có **schema XML chuẩn** (MST bên bán/mua, mẫu số, ký hiệu, từng dòng hàng-tiền-thuế suất-tiền thuế, tổng, chữ ký số). ⇒ **trích xuất phần lớn là DETERMINISTIC parse XML — KHÔNG để LLM bịa số** (khớp hoàn hảo invariant #3). Đây là lý do **AP automation cho VN DỄ + ĐÁNG TIN hơn** OCR hoá đơn giấy phương Tây (vốn là phần khó/đắt nhất của AP). *(Bản scan/PDF cũ → Docling/OCR + LLM extract + verify-gate.)*
> ⚠️ Cần lấy **bản schema XML chính thức** (TT78 phụ lục) + xác nhận với kế toán BRAVO.

## 1. Kiến trúc tổng — deterministic backbone + LLM-in-slot + HITL
```
Nguồn (XML hoá đơn / tờ khai / sổ ERP)
  → [DETERMINISTIC] parse XML hoá đơn (LLM chỉ khi scan/PDF)
  → [DETERMINISTIC] validate: MST hợp lệ · Σ dòng = tổng · thuế suất ∈ {0,5,8,10%} · trùng số
  → [LLM-GỢI-Ý + catalog] map tài khoản TT99 (rule quyết định; LLM chỉ gợi ý khi mơ hồ)
  → [DETERMINISTIC] dựng bút toán nháp, cân Nợ=Có (calc Decimal, reconciliation gate — ĐÃ CÓ)
  → [DETERMINISTIC] verify-gate: mọi số khớp hoá đơn nguồn + trích dẫn (ĐÃ CÓ)
  → [DETERMINISTIC] cross-check: hoá đơn ↔ tờ khai ↔ sổ → bắt sai lệch
  → [HITL] draft chờ duyệt (maker-checker, anti-self-approval — ĐÃ CÓ)
  → (sau duyệt) đẩy ERP staging (chờ API ghi)
```
**Nguyên tắc:** LLM KHÔNG sinh số, KHÔNG tự hạch toán/nộp tờ khai — chỉ gợi ý map + diễn giải + tạo *nháp*. Số từ XML/calc; người duyệt quyết.

---

## 2. Use-case A — AP: hoá đơn đầu vào → định khoản nháp ($ rõ nhất)
- **Input:** hoá đơn điện tử XML (cấu trúc) hoặc PDF/scan (Docling+OCR).
- **Trích xuất:** XML → deterministic (MST, dòng hàng, tiền hàng, VAT, tổng). Scan → LLM extract + verify.
- **Map TK (TT99):** theo loại hàng/dịch vụ + nhà cung cấp + lịch sử bút toán → gợi ý TK chi phí/hàng (152/156/211/627/641/642...) + **VAT đầu vào TK 1331**. Rule + catalog quyết; LLM chỉ gợi ý khi mơ hồ; người sửa được.
- **Dựng bút toán:** `Nợ <chi phí/hàng> + Nợ 1331 / Có 331 (phải trả NCC)` — cân Nợ=Có (calc Decimal).
- **Verify-gate:** mọi số khớp hoá đơn nguồn; trích dẫn tới hoá đơn (số/ký hiệu/dòng).
- **HITL:** draft chờ kế toán duyệt (maker-checker).
- **ROI:** số hoá đơn/giờ · **% nháp duyệt-không-sửa** · giảm $/hoá đơn (benchmark ~4x) · giảm sai sót nhập liệu.
- **bravo có/thiếu:** ✅ draft+maker-checker · verify · calc Decimal · citations | ❌ **parser hoá đơn XML · map-TK engine · UI review**.

## 3. Use-case B — Cross-check hoá đơn ↔ tờ khai ↔ sổ (MOAT — ngoại không làm được)
- **Đối chiếu:** doanh thu sổ ↔ tờ khai GTGT/TNDN; hoá đơn đầu vào ↔ bảng kê tờ khai; tổng khớp.
- **Bắt sai lệch:** hoá đơn bỏ sót/khai thiếu · sai MST · sai thuế suất · **hoá đơn rủi ro (NCC bỏ trốn/ngừng hoạt động)** · trùng · lệch kỳ.
- **Cơ chế:** engine deterministic TÍNH sai lệch (như anomaly); **LLM chỉ diễn giải + xếp hạng rủi ro + trích dẫn**; tạo **draft kiến nghị điều chỉnh** (không tự sửa).
- **Vì sao ngoại không làm:** cần hiểu **schema hoá đơn điện tử VN + mẫu tờ khai VN + quy tắc thuế VN** — AI ngoại (SAP/Oracle/MISA-cloud) không có.
- **ROI:** số sai lệch bắt được · **tránh phạt thuế** · rút ngắn thời gian quyết toán/giải trình.
- **bravo có/thiếu:** ✅ verify-gate · draft · RLS | ❌ **engine đối soát · hiểu mẫu tờ khai · tra cứu NCC rủi ro**.

## 4. Use-case C — Di trú hệ tài khoản TT99 (deadline 1/1/2026 ép cầu)
- **Việc:** map TK cũ TT200 → TT99 (research đã xác nhận: rename TK112/242; bỏ TK417/441/461/466/611/631; thêm TK332/2414/2295); chuyển số dư đầu kỳ; cảnh báo TK bỏ/gộp; sinh **bút toán chuyển đổi** chờ duyệt.
- **Cơ chế:** **bảng map TT200→TT99 deterministic** (lấy từ phụ lục TT99) + LLM giải thích thay đổi; verify số dư sau chuyển = trước chuyển.
- **ROI:** số TK map tự động · thời gian di trú · tránh sai sót khoá-sổ-chuyển-kỳ · **đáp ứng deadline pháp lý**.
- **bravo có/thiếu:** ✅ calc Decimal · verify · draft | ❌ **bảng map TT200→TT99 · engine chuyển số dư**.

---

## 5. Ranh giới — chỗ AI KHÔNG tự quyết (judgment + governance)
- **Map TK mơ hồ / phân loại chi phí có judgment / hoá đơn rủi ro cao → HITL bắt buộc** (draft, người quyết).
- **LLM KHÔNG sinh số** — số từ XML/calc deterministic; verify-gate chặn số bịa.
- **Không tự nộp tờ khai / tự hạch toán** — chỉ draft; tôn trọng **kỳ đã khoá sổ**; bút toán phải cân Nợ=Có (journal-validator — backlog ADR).
- Hoá đơn rủi ro/NCC bỏ trốn = **cờ đỏ cho người**, không tự loại.

## 6. Tái dùng bravo (đòn bẩy — đừng xây lại)
| Thành phần engine | bravo ĐÃ CÓ | Cần thêm |
|---|---|---|
| Số không bịa | ✅ verify-gate + calc Decimal | — |
| Cân Nợ=Có | ✅ reconciliation gate | journal-entry validator (backlog ADR) |
| Ghi = nháp chờ duyệt | ✅ draft + maker-checker | UI review (PRODUCT-SURFACE PS-3) |
| Trích dẫn nguồn | ✅ citations | trích tới dòng hoá đơn |
| Phân quyền | ✅ RLS-in-SQL | scope theo phòng/đơn vị |
| Bóc tài liệu | ⚠️ Docling (chưa cài) | parser XML hoá đơn (mới, deterministic) |
| Map TK / đối soát | ❌ | **catalog TT99 + rule map + cross-check engine** |

## 7. Lộ trình build — cái nào làm NGAY (không cần ERP)
- **Làm NGAY (chỉ cần hoá đơn mẫu XML + bảng TK):** parser hoá đơn điện tử → validate → map-TK catalog TT99 → dựng bút toán nháp → verify (tất cả cắm vào draft/verify/calc ĐÃ CÓ). ⇒ **demo AP chạy trên hoá đơn THẬT, KHÔNG cần ERP** — đây là use-case "đinh" demo được sớm nhất với $ rõ.
- **TT99 migration:** cần bảng số dư (mock được trước, ERP thật sau).
- **Cross-check:** cần tờ khai + sổ (cần ERP/dữ liệu thuế — sau).

## 8. Demo bán + metric ROI (2-3 kịch bản)
1. **🔥 Thả 10 hoá đơn điện tử XML → 10 bút toán nháp** (cân Nợ=Có, map TK, VAT 1331) → kế toán Review/Approve. Metric: phút/hoá đơn, % duyệt-không-sửa.
2. **🛡️ Cross-check tháng:** đối chiếu hoá đơn–tờ khai GTGT → bắt 2 sai lệch (1 hoá đơn bỏ sót, 1 NCC rủi ro) → draft kiến nghị. Metric: số sai lệch bắt được, tránh phạt.
3. **📒 Di trú TT99:** map TK cũ→mới + chuyển số dư + bút toán chuyển đổi chờ duyệt. Metric: số TK map tự động, đáp ứng deadline.

## 9. Phụ thuộc & cảnh báo trung thực
- **Cần (kiểm chứng/lấy thật):** schema XML hoá đơn điện tử (TT78 phụ lục) · **bảng map TT200→TT99 chính thức** (TT99 phụ lục) · mẫu tờ khai GTGT/TNDN · API tra cứu MST/NCC rủi ro (Tổng cục Thuế) · ERP write staging (Phase 3).
- **Cần kế toán BRAVO xác nhận:** quy tắc map TK theo loại hàng/ngành · ngưỡng cross-check · xử lý thuế suất đặc thù.
- **ROI = kỳ vọng phải chứng minh qua pilot** (chưa có hoá đơn/ERP thật chạy).
- **Liên quan VAS/IFRS & TT99 (ĐÃ research — [research/VAS-IFRS-MONEY-SPOTS.md](research/VAS-IFRS-MONEY-SPOTS.md)):** money-spot gần-hạn THẬT là **tuân thủ TT99** (đã chốt 1/1/2026, phổ cập, **cơ học ít-judgment**) → **GỘP vào engine này** (use-case D mới): (i) **remap CoA cấp ≥2 + sinh nháp "Accounting Policy Regulation" bắt buộc**; (ii) **bù-trừ hợp nhất nội bộ** (đầu mối + đơn vị phụ thuộc). Lớp **VAS↔IFRS đầy đủ** (mapping/dual-ledger/disclosure) = **agent TÁCH RIÊNG giai-đoạn-sau** (judgment-heavy: fair value/impairment → CHỈ có-người-duyệt; phạm vi hẹp niêm yết/FDI; cần pilot chứng minh ROI). **Moat:** verify-gate + maker-checker + audit-trail = điều kiện *"AI tài chính kiểm-toán-được"* (Big4/EU AI Act 8/2026) — bán được niềm tin.

---
> Thiết kế này biến 2 "chỗ ăn tiền" thành một sản phẩm tận dụng ~70% cái bravo đã có (đuôi close-the-loop) + xây phần đầu VN-native mà đối thủ ngoại không có. Use-case A demo được **không cần ERP** = đường nhanh nhất tới một demo có $ rõ.
