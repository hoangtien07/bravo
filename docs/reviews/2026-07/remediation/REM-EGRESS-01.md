# REM-EGRESS-01 — Server-authoritative ingest sensitivity

Status: Complete

## Failure reproduced

`ingest_sensitive` previously treated an unlabeled department-scoped upload as non-sensitive. The upload route also forwarded caller-supplied `knowledge_type` into ingestion, allowing untrusted request metadata to affect embedding egress.

## Change

- `app/api/routes_sources.py:upload_source` passes no trusted classification for runtime uploads.
- `app/ingestion/pipeline.py:ingest_source` accepts `trusted_knowledge_type` only for trusted corpus callers and persists `extra.is_sensitive` onto every chunk.
- `app/security/sensitivity.py:ingest_sensitive` treats missing trusted classification as sensitive regardless of department scope.
- `scripts/ingest_userguide.py` explicitly supplies its manifest-derived trusted classification.

## Tests

`python -m pytest -q tests/test_sensitivity.py tests/test_egress_embedding.py tests/test_router_egress.py tests/test_rerank_egress.py` — 20 passed.

The tests use fake providers; no production credential or provider was used.

## Compatibility and rollback

Existing manifest ingestion continues to pass its manifest classification. Runtime uploads without a trusted classification now use local/sensitive handling. No schema, migration, or config change. Rollback is not safe while cloud embedding is enabled unless the zero-egress regression remains enforced by another control.

## Remaining risk

The actual provider receipt/network audit is still operational evidence, not a substitute for the tested call-path control.
