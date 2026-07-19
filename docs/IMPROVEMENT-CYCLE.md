# Vòng cải thiện chất lượng (D4) — từ flag của team đến sửa có bằng chứng

> Cách biến "team flag câu trả lời tệ" thành "đã sửa, đo được, không regression". Lặp hàng tuần.
> Đây là ritual người vận hành (kế toán trưởng/IT/dev) làm — không tự động promote gì vào KB (QĐ-5).

## Nhịp hàng tuần (4 bước)

### 1. Gom flag
- Vào **Quản trị → Phản hồi chất lượng** (câu bị 👎/báo lỗi) — hoặc CLI:
  `python -m scripts.export_feedback > feedback.yaml`.
- Tín hiệu bổ sung (CORPUS-OPS §1): `bravo_retrieval_zero_hits_total`, `bravo_answer_outcomes_total{outcome=abstain}`,
  `bravo_ungrounded_numbers_total` trên `/metrics`.

### 2. Phân nhãn mỗi case (CORPUS-OPS §2)
- `corpus-miss` — thiếu tài liệu (retrieval 0 hit / abstain dù đáng lẽ có).
- `retrieval-miss` — có tài liệu nhưng không kéo lên (rerank/intent/min_score).
- `synthesis-poor` — kéo đúng nhưng trả lời dở (prompt).
- `wrong-task-type` — chọn sai profile/workflow.

### 3. Sửa MỘT cụm (đừng ôm hết)
- `corpus-miss` → thêm nguồn vào [file_system/bravo_corpus_manifest.yaml](../file_system/bravo_corpus_manifest.yaml) →
  `python -m scripts.ingest_userguide ./file_system` → `python scripts/backfill_chunk_sensitivity.py --apply`.
- `retrieval-miss` → chỉnh intent hint ([bravo_intent.py](../app/rag/bravo_intent.py)) / `rerank_pool_size` / `retrieval_min_score`.
- `synthesis-poor` → chỉnh prompt ([grounded_answer.py](../app/rag/grounded_answer.py) SYSTEM/GUARDED_SYSTEM).
- `wrong-task-type` → chỉnh workflow trigger/card ([bravo_consultant_cards.yaml](../file_system/bravo_consultant_cards.yaml)).

### 4. Đo lại (bằng chứng trước/sau, chống regression)
- **Trên chính các câu đã flag** (nhanh, đúng trọng tâm):
  ```bash
  python -m app.eval.ab_c0_compare --username <admin@..> --from-feedback --max-questions 30 --out after.json
  ```
  So A(legacy)/B(consultant)/C0(bare) side-by-side; đối chiếu `before.json` chạy trước khi sửa.
- **Parity vs BravoGen** (cổng ship ≥45% win+tie — CORPUS-OPS §3):
  `python -m app.eval.parity_bench app/eval/parity_questions.yaml > parity_run.json` → chấm mù 2 người.
- **Regression toàn cục:** `python -m app.eval.run --passk --mock --k=8` phải PASS (hard-fail detectors).
- Câu đã sửa → thêm vào golden set để không tái phát.

## Ranh giới (QĐ-5)
- Được tự động: gom flag, đo, đề xuất. **Không** tự động: đẩy nội dung vào KB, đổi RLS/egress/ngưỡng gate —
  đều qua người duyệt. Flag/feedback có thể chứa dữ liệu cá nhân → xử lý theo PDPL, đặt retention.

## Khi nào leo thang kiến trúc (không làm sớm)
- Nếu sau vài vòng, phần lớn thua là **synthesis/prerequisite** mà C0 (model trần + evidence) cũng thua →
  cân nhắc V2 core (P3). Nếu C0 đã đủ tốt → dồn sức vào **evidence/corpus**, không xây core (stop-rule QĐ-4).
