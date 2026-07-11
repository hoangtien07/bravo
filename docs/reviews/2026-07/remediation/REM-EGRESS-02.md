# REM-EGRESS-02 — Sensitivity-aware rerank egress

Status: Complete

## Failure reproduced

The LLM reranker built a prompt from retrieved chunks and called the router with `sensitive=False`, allowing a configured cloud provider to receive scoped/private passage text.

## Change

- `app/rag/retriever.py:Retrieved` now carries `is_sensitive`, defaulting unknown legacy metadata to sensitive.
- `vector_search` and `lexical_search` propagate chunk sensitivity metadata.
- `retrieve` skips cloud LLM reranking whenever any candidate in the cloud rerank pool is sensitive or unknown.
- `app/rag/rerank.py:llm_rerank` requires explicit sensitivity and passes it to the router.

## Tests

`python -m pytest -q tests/test_sensitivity.py tests/test_egress_embedding.py tests/test_router_egress.py tests/test_rerank_egress.py` — 20 passed.

`tests/test_rerank_egress.py` proves the sensitive branch makes zero fake-cloud calls and that the low-risk branch transmits an explicit router classification.

## Compatibility and rollback

No migration or provider-config change. Sensitive/unknown candidates retain fused order instead of cloud reranking; local cross-encoder behavior is unchanged. Do not roll back while cloud LLM rerank is enabled.

## Remaining risk

Chunk metadata from pre-existing data without `is_sensitive` remains intentionally fail-closed; a trusted data-classification migration is outside this package.
