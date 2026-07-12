# CORPUS-OPS — vòng đời corpus & đo chất lượng trả lời (v2, Q4/Q10)

Trả lời câu hỏi: *làm sao biết bravo trả lời kém ở đâu, và biến điều đó thành việc cần làm?*
Council 2026-07-12 chỉ ra ~40% điểm thua BravoGen là **lỗ hổng corpus** (dữ liệu không có),
không phải retrieval. Không quy trình nào tự đóng lỗ đó — cần một nghi thức lặp.

## 1. Ba tín hiệu gap (thu tự động)

| Tín hiệu | Nguồn | Ý nghĩa |
|---|---|---|
| **Zero-hit retrieval** | log `bravo.rag` dòng `retrieval.gap` (retriever.py) | câu hỏi không kéo được chunk nào → corpus thiếu hoặc từ khoá lệch |
| **Dislike feedback** | `scripts/export_feedback.py` → YAML | người dùng chấm câu trả lời tệ |
| **Abstain rate** | đếm câu trả lời mở đầu "Không tìm thấy…" | phần câu hỏi corpus không phủ |

## 2. Nghi thức hàng tuần

1. **Gom gap**: `grep 'retrieval.gap' <log>` + `python -m scripts.export_feedback > feedback.yaml`.
2. **Phân nhãn** mỗi gap: `corpus-miss` (thiếu dữ liệu) · `retrieval-miss` (có dữ liệu, không kéo lên) · `synthesis-poor` (kéo đúng, trả lời dở) · `wrong-task-type` (chấm sai vai).
3. **`corpus-miss` → acquisition**: chủ nhiệm dữ liệu export tài liệu/danh mục còn thiếu → thêm vào `file_system/bravo_corpus_manifest.yaml` → re-ingest. (Ví dụ đang chờ: danh mục **mã giao dịch** — "Giao dịch 2103" = 0 chunk; 50–100 cặp Q&A helpdesk → `support_ticket`; tài liệu "mua hàng công nợ".)
4. **`retrieval-miss` → tune**: thêm câu vào golden set, chỉnh intent boost / min_score / abbreviation.
5. **`synthesis-poor` → prompt**: chỉnh `_SYSTEM`/`_COMPOSE_SYSTEM`; thêm vào parity benchmark.
6. **Câu đã sửa → golden set** (`app/eval/golden_set_bravo*.yaml`) để không regression.

## 3. Parity benchmark vs BravoGen (Q4)

- **Bộ câu hỏi**: `app/eval/parity_questions.yaml` (mẫu: `.example.yaml`) — phân tầng theo nhóm nghiệp vụ (nhập chứng từ / báo cáo / khoá sổ / lỗi thường gặp), lấy từ log pilot + phàn nàn council.
- **Chạy bravo**: `python -m app.eval.parity_bench app/eval/parity_questions.yaml > parity_run.json` (dùng đúng cấu hình prod: rerank theo settings, top_n=12).
- **Chạy BravoGen**: thu thủ công (không có API) → điền `bravogen_answer`.
- **Chấm mù**: 2 người (helpdesk + triển khai), rubric:
  - đúng nghiệp vụ BRAVO · đầy đủ · khả thi thao tác · **trung thực nguồn** (world-knowledge KHÔNG nhãn = thua tự động).
  - điền `verdict` = win|tie|loss, `failure_label` cho mỗi ca thua.
- **Cổng ship**: **≥45% win+tie**; đo lại hàng tháng. Ghim ngày so sánh (BravoGen là mục tiêu di động).

## 4. Cổng chất lượng (CI)

- Citation ≥95% + refusal đúng: `python -m app.eval.run <golden.yaml>` (đã khớp cấu hình prod — Q4).
- 0 rò RLS: `app/eval/probes.py::assert_no_leak` + pass^k `--passk`.
- **Stop-rule (ADR-0020)**: khi citation ≥95% + parity ≥ hoà + first-token <3s → DỪNG đánh bóng Q&A, quay lại track AP.
