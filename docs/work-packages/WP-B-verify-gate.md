# WP-B — Verify-gate: value-object + Decimal + reconciliation

> Module: `app/data_layer`. **Đọc [CONTRACTS.md](CONTRACTS.md) trước.** Hiện thực [ADR-0012](../adr/0012-verify-gate-number-integrity.md). Phụ thuộc: CONTRACTS (MetricResult).

## Mục tiêu
Biến verify-gate từ code-chết thành **gate cứng**: mọi số trả về phải khớp giá trị engine (đúng cả **đơn vị/bội số**), tiền là **Decimal**, tổng khớp chi tiết. Đây là **BLOCKING** cho mọi đường trả lời có số.

## Reuse (ADR-0013)
REWRITE — phần độc quyền BRAVO (nghiệp vụ số VN). Không repo nào có. `calc.py` đã có safe-AST sandbox — **giữ**, chỉ đổi float→Decimal.

## Scope IN / OUT
**IN:** định nghĩa `MetricResult` value-object (CONTRACTS §2.3); `verify_numbers(answer, engine_values) -> VerifyVerdict`; chuẩn hoá về VND base trước khi so; chặn LLM đổi tỷ↔triệu; `Decimal` + `ROUND_HALF_UP` trong calc; reconciliation `Σ(chi tiết)==tổng` (dung sai 0 đồng); parse số tiếng Việt khử nhập nhằng `2.337` (=2337) vs thập phân ([grounding.py:34-44] đã có khung).
**OUT (đừng làm):** wiring vào loop (đó là việc WP-D — WP-B chỉ cung cấp hàm); "LLM tự verify số" (schema-valid ≠ số đúng); đổi đơn vị bằng LLM (đổi đơn vị = phép tính ở calc).

## Files
`app/data_layer/semantic.py` (MetricResult value-object thay float) · `grounding.py` (`verify_numbers` + VerifyVerdict) · `calc.py` (Decimal).

## Việc cụ thể
1. `MetricResult` theo CONTRACTS §2.3 (`value: Decimal`, `unit/scale/currency/period/entity/variant/provenance/is_demo`).
2. `verify_numbers`: trích mọi token số trong `answer`; chuẩn hoá answer-number + engine-value về **cùng base (đồng VND)** dùng `scale`; mỗi số answer phải khớp **đúng một** engine value (không "bất kỳ × bất kỳ"); không khớp → đưa vào `unmatched` + mask trong `safe_answer`.
3. `calc.py`: `Decimal`; chia/tỷ-lệ giữ Decimal, `quantize` bước cuối (VND 0 chữ số thập phân, ngoại tệ 2).
4. `reconcile(total, parts) -> bool`: `Σ parts == total` (Decimal, dung sai 0).

## Acceptance (test)
- engine `MetricResult(value=Decimal("12.5"), scale="tỷ")`, answer ghi "12,5 **triệu**" → `grounded=False`, số bị mask.
- answer chỉ chứa số khớp engine → `grounded=True`.
- cross-foot: `reconcile(tổng, [chi tiết...])` True khi khớp, False khi lệch 1 đồng.
- float-drift: phép cộng tiền cũ (float) cho kết quả lệch → test fail; sau Decimal → pass.

## Invariant
#3 (cưỡng chế zero-hallucination số — chặn sai bội số & tổng không cân).

## Phụ thuộc
CONTRACTS (MetricResult). WP-D sẽ **gọi** `verify_numbers` trong loop (seam ở CONTRACTS §3).
