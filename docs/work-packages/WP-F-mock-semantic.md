# WP-F — Mock DataSource + semantic-RLS + catalog TT99 + metric-variants

> Module: `app/data_layer`. **Đọc [CONTRACTS.md](CONTRACTS.md) + [MOCK-DATA-SPEC.md](../MOCK-DATA-SPEC.md) trước.** Phụ thuộc: WP-B (MetricResult).

## Mục tiêu
Cho Demo B chạy hỏi-đáp số **không cần ERP**: `MockDataSource` trả `MetricResult` (TT99, nhãn DEMO), semantic layer **áp RLS** + **whitelist metric** (LLM không sinh SQL), khai báo **biến thể** + reconciliation.

## Reuse (ADR-0013)
REWRITE — phần độc quyền (nghiệp vụ TT99). Semantic layer ERP-agnostic ([semantic.py]) đã có khung — chỉ thêm `identity` + value-object + mock source. Khi ERP thật về → viết `BravoErpDataSource` cùng Protocol, đổi 1 dòng cấu hình.

## Scope IN / OUT
**IN:** `DataSource.fetch(metric_id, params, identity)` (CONTRACTS §2.4); `MockDataSource` đọc `tests/fixtures/mock_financials_tt99.yaml`; **áp RLS theo identity** (metric nhạy như `quy_luong_thang` chỉ cho `nhansu`/`giamdoc`); metric khai `scope_columns` → **fail-at-load nếu thiếu scope-binding**; mỗi metric khai **variant** (gộp/thuần, đã/chưa VAT...); `clarify` khi câu hỏi mơ hồ giữa biến thể; reconciliation gate (gọi WP-B `reconcile`); ngoài whitelist → **ABSTAIN**.
**OUT (đừng làm):** `erp/client` thật (deferred); Cube/OLAP đầy đủ (whitelist + ABSTAIN là vừa đủ); SQL tự do; nhiều hơn ~18 metric ([METRIC-CATALOG-PROPOSAL.md] đã có).

## Files
`app/data_layer/semantic.py` (DataSource+identity, register fail-at-load) · `catalog.py` (đăng ký ~18 metric + scope_columns + variant) · `app/data_layer/mock_source.py` (mới) · `tests/fixtures/mock_financials_tt99.yaml` (mới — theo MOCK-DATA-SPEC §3).

## Việc cụ thể
1. `DataSource` Protocol thêm `identity`; `execute/answer` truyền identity.
2. `MetricRegistry.register`: bắt buộc `scope_columns` (department_id/unit_id/period) + `variant`; thiếu → raise tại import.
3. `MockDataSource.fetch`: đọc yaml → `MetricResult` (Decimal, scale, variant, `is_demo=True`); áp RLS (metric nhạy + identity không quyền → raise/abstain).
4. Cài sẵn dữ liệu bất thường (hoá đơn trùng, số tròn) cho demo soi bất thường nhẹ — LLM chỉ xếp hạng/diễn giải.
5. `plan_fn` (LLM map câu hỏi→metric) qua structured-output (WP-D); ngoài whitelist → None → ABSTAIN.

## Acceptance (test)
- register metric thiếu `scope_columns` → fail tại load.
- `fetch` không `identity` → fail; user `kinhdoanh` hỏi `quy_luong_thang` → abstain/deny (RLS tầng số).
- câu mơ hồ biến thể ("doanh thu?" thiếu kỳ/biến thể) → clarify, không đoán.
- tổng ≠ Σ chi tiết → reconciliation từ chối.
- câu ngoài whitelist metric → ABSTAIN (không SQL tự do).

## Invariant
#1 (RLS tầng số) · #3 (whitelist+ABSTAIN, không sinh SQL/số; variant chống nhầm nghĩa).

## Phụ thuộc
WP-B (MetricResult, reconcile). ⚠️ Ngữ nghĩa metric thật (gross/net, VAT, kỳ khoá sổ) **cần kế toán BRAVO xác nhận** trước khi nối ERP thật — demo dùng nhãn DEMO nên không chặn.
