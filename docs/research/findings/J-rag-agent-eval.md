# Findings J — Permission-aware RAG, bộ công cụ RAG, Memory, HITL, Eval

> Lấp khoảng trống Track B (RLS-on-vector học thuật, chất lượng RAG, memory, HITL, eval). Agent đọc arXiv/ACL + Anthropic/Letta/OpenAI docs, 2026-06-08.

## 1. Permission-aware / multi-tenant RAG — RLS-on-vector ĐƯỢC HỌC THUẬT ỦNG HỘ
- **"Relevance-authorization gap":** truy hồi xếp theo *độ liên quan*, không theo *quyền* → cần đồng thời ngưỡng liên quan **VÀ** vị từ ủy quyền.
- **Gating trong query = 0% rò; không gating = 62–80% truy vấn dò trả dữ liệu trái phép** (arXiv 2605.05287).
- 🔴 **Lọc post-retrieval sụp recall theo quy mô:** Recall@5 = 1.000 (100 tài liệu) → **0.002 (50.000 tài liệu)**. → **PHẢI lọc trong query** (predicate pushdown). **pgvector/Qdrant/Milvus** nằm trong danh sách khuyến nghị. → **Tiền lệ Supabase RLS-on-pgvector của BRAVO được ủng hộ trực tiếp.**
- **Participant-aware:** kiểm quyền *mọi bên* trong nội dung, không chỉ người hỏi (tài liệu có thể chứa dữ liệu bên thứ ba).
- **Không lọc ở tầng LLM** (anti-pattern, dễ prompt-injection) — lọc deterministic ở DB *trước khi* context tới model.
- **Rủi ro vận hành:** quyền cũ tồn dư tới lần re-index; bản ghi xóa vẫn nằm dạng embedding → cần **tombstone + webhook**.

## 2. Bộ công cụ chất lượng RAG (xếp theo ROI có bằng chứng)
1. 🥇 **Reranking (đòn bẩy lớn nhất):** Cohere reranker, top-150 → top-20. Giảm thất bại truy hồi **−67%** (Anthropic); **+17.4 điểm** Recall@5 (arXiv 2604.01733).
2. 🥈 **Hybrid BM25 + vector + RRF:** trên tài liệu tài chính **BM25 (0.644) VƯỢT dense (0.587)** — *"lexical matching đặc biệt hiệu quả cho tài chính, nơi thuật ngữ chính xác (tên công ty, mã chỉ số, kỳ) là tín hiệu mạnh mà embedding làm loãng."* → **bắt buộc cho mã chứng từ/số/tên riêng.**
3. 🥉 **Contextual Retrieval (Anthropic):** prepend ngữ cảnh mỗi chunk → gain nhất quán (+2.2đ), rẻ với prompt caching ($1.02/triệu token).
- ColBERT chỉ khi QPS cao; HyDE/multi-query để dành câu phức tạp (KXM lợi ích định lượng).

## 3. Memory agent — TỰ XÂY LÕI GỌN, không full Letta
- Pattern MemGPT: **core** (in-context, sửa bằng tool) / **recall** (lịch sử, search) / **archival** (vector dài hạn). Context đầy → **evict ~70% + tóm tắt đệ quy** (không mất dữ liệu). Ý tưởng **sleep-time** (cập nhật bộ nhớ nền).
- **Khuyến nghị:** tự xây lõi gọn theo pattern này **trên pgvector sẵn có** vì (a) áp được **RLS của BRAVO lên archival** (Letta là store riêng, khó áp RLS), (b) tránh thêm service stateful. Chuyển thể code từ letta (Apache 2.0) ở mức module.

## 4. Human-in-the-loop & approval (cho mọi tool ghi)
- **`requires_approval` + pause → serialize state vào DB → resume sau duyệt** (OpenAI Agents SDK pattern).
- 🔴 **Pin args theo hash:** args có thể đổi giữa lúc duyệt và lúc chạy (agent re-run LLM) → pin payload theo hash, **từ chối nếu hash lệch**.
- **Tiered approval** (Allow Once/Always/Decline) chống "confirmation fatigue" (over-approval là lỗ hổng bảo mật).
- Đặt validation **ngay cạnh tool tạo side-effect**, tách read (auto) / write (approval).

## 5. Eval stack (CI chống regression)
- **DeepEval/RAGAS làm unit-test gate trong CI mỗi PR** — tách metric **retriever** (contextual recall/precision) vs **generator** (faithfulness, answer relevancy). Chỉ chuẩn bị input+expected, chạy app tại thời điểm eval.
- **BEIR/golden-set** offline cho retrieval quality; **RAGTruth** (ACL 2024, ~18k response annotate span-level — *fine-tune LLM nhỏ phát hiện hallucination ngang GPT-4*) cho detector; **ARES** (PPI, độ tin cậy thống kê) định kỳ.
- Thêm **probe test rò chéo ACL** (§1) + **freshness check** KB.
- *Lưu ý:* RAGAS tương quan với người chỉ ~0.55 → không dùng độc lập tuyệt đối.

## 6. 🎯 Khuyến nghị tổng hợp (→ ARCHITECTURE + ADR model)
| Hạng mục | Chốt |
|---|---|
| RLS | Lọc ACL **trong query** trên pgvector + participant-aware + CI probe rò chéo + tombstone |
| Rerank | **Có** (ưu tiên #1) — Cohere/ViRanker |
| Hybrid | **Có** — BM25+vector+RRF (bắt buộc cho số/mã) |
| Contextual Retrieval | Nên (rẻ, gain nhất quán) |
| Memory | **Tự xây lõi gọn** (MemGPT pattern) trên pgvector, không full Letta |
| HITL | draft→approve, `requires_approval` + **pin args hash** + tiered |
| Eval | DeepEval/RAGAS CI + BEIR/golden + RAGTruth + ARES + probe rò + freshness |

## Cảnh báo độ tin cậy
- arXiv 2605.05287: abstract ghi "98–100% rò" mâu thuẫn bảng (62–80%) → dùng số bảng; preprint kiểu 2026 chưa rõ peer-review.
- Taxonomy RAGTruth + latency ColBERT chỉ ở nguồn secondary. HyDE/multi-query KXM định lượng.

## Nguồn
arXiv 2605.05287, 2509.14608 (perm-RAG) · Anthropic Contextual Retrieval · arXiv 2604.01733 (rerank/hybrid finance) · MemGPT paper + Letta docs · OpenAI Agents SDK HITL · ARES 2311.09476 · RAGTruth ACL 2024.acl-long.585 · DeepEval (Confident AI).
