# T3 — RAG & Ingestion Pipeline

Scope read: T0, T2, and T6 artifacts; `app/ingestion/**`, `app/rag/**`, `scripts/ingest_userguide.py`, corpus manifest/policy, and direct ingestion/retrieval tests. No ingestion, vector, or retrieval test was run because the host Python toolchain is unavailable.

## Ingest → retrieval trace

| Stage | Implementation evidence | Scope/metadata effect |
|---|---|---|
| Source creation | API upload creates `Source` plus caller-supplied `SourceDepartment`; CLI creates a source and optionally one department row. | T2/T1 establish the API write-scope weakness; CLI default is global. |
| Shared-corpus selection | `scripts.ingest_userguide._select_files` is manifest-only by default and rejects an absent/invalid manifest. | Manifest metadata is passed as `source_extra`; explicit `--allow-unmanifested` bypasses this mode. |
| Parse/chunk | `ingest_source` dispatches parser, heading-chunks text PDFs, token-chunks other long blocks, then embeds. | Parser retains optional page/sheet/cell/heading; tables are not split. |
| Scope propagation | `ingest_source` queries `SourceDepartment.department_id` and writes the resulting list to every `Chunk.department_ids`. | Caller-assigned source scope is retained on chunks. |
| Retrieval | Dense and lexical queries both call `chunk_scope_filter(identity, "read")` before ranking; RRF fuses results, then optional rerank runs. | Department is a structured SQL pre-filter; source type/module/lifecycle metadata is only a post-retrieval score boost. |
| Response/citation | `Retrieved` exposes source UUID, page/sheet/cell, score, and `extra`; `citation()` formats source ID/page/sheet/cell. | Heading is stored on `Chunk` but is not projected into `Retrieved`/citation. |
| Abstention | `retrieve` returns `[]` when no fused candidates; T1's `/ask` returns a refusal for empty retrieval. | Agent behavior for empty retrieval is T4 scope. |

## Metadata classification

| Category | Fields/evidence | Assessment |
|---|---|---|
| Required for stored chunk | `source_id`, `content`, `embedding`, `department_ids` (`Chunk` model/pipeline) | VERIFIED storage/scope fields |
| Optional provenance | `page_number`, `sheet_name`, `cell_range`, `heading_path`, parser `extra` | VERIFIED as optional; availability depends on parser path |
| Derived manifest metadata | `source_extra` copies manifest metadata except knowledge type into `Chunk.extra`, including relative path and taxonomy values | VERIFIED for CLI manifest ingestion; direct API uploads pass no manifest extra |
| Derived ranking hints | `source_type`, `module`, `lifecycle_stage` read from `Retrieved.extra` by `boost_for_bravo_intent` | VERIFIED post-retrieval boost, not filter |
| Not represented as source/chunk metadata | Source-content hash, immutable source version, ingest timestamp, tombstone/version lineage | VERIFIED absent from `Source`/`Chunk` model and pipeline path |

## Findings

| ID | Severity tạm thời | Evidence state | File:symbol | Evidence ngắn | Consumer/impact | Next action | Needs Sol review |
|---|---|---|---|---|---|---|---|
| BRV-API-002 | High | VERIFIED | `app/ingestion/pipeline.py:ingest_source`; `app/rag/retriever.py:vector_search`, `lexical_search` | Pipeline copies all `SourceDepartment` IDs to `Chunk.department_ids`; both retrieval branches enforce `chunk_scope_filter` over that copied value. | T2's source write/read finding is now confirmed end-to-end through chunk retrieval: an unauthorized caller-assigned source scope becomes an unauthorized retrieval scope. | Retain ID; Sol review remains required. Remediation must constrain source write scope before ingestion; no separate T3 finding for the same failure path. | Yes |
| BRV-RAG-001 | High (conditional) | VERIFIED | `app/api/routes_sources.py:upload_source`; `app/ingestion/pipeline.py:ingest_source`; `app/security/sensitivity.py:ingest_sensitive` | Upload accepts caller-controlled `knowledge_type`; pipeline uses it plus caller-derived department assignment to choose `sensitive` before cloud embedding. A global upload labelled with a non-sensitive type bypasses the “global + unknown” fail-closed branch. | With cloud embedding enabled, a document's private/shared classification can be controlled at ingest entry and the content may egress. | Sol decide trusted classification authority; T6 cloud-embedding guard is insufficient without trusted source metadata. Add adversarial upload classification coverage. | Yes |
| BRV-RAG-002 | High (conditional) | VERIFIED | `scripts/ingest_userguide.py:_select_files`, `main` | `--allow-unmanifested` returns all ingestible files, while `department` remains optional; `main` creates no `SourceDepartment` row when it is omitted. | An operator can explicitly import unmanifested files as global shared corpus. This defeats the intended private/shared separation for that CLI path. | Require a non-global scope for unmanifested imports or reject them from shared corpus; Sol review is needed for the private/shared ingestion policy. | Yes |
| BRV-RAG-003 | Medium | VERIFIED | `scripts/ingest_userguide.py:main`; `app/ingestion/pipeline.py:ingest_source`; `app/database/models.py:Source`, `Chunk` | Reindex selection deletes all rows with matching `Source.filename`; no source hash, relative-path uniqueness, version, tombstone, or ingest timestamp is stored. Pipeline deletes old chunks before parsing/embedding replacement succeeds. | Same-basename sources can be deleted/replaced together, and a failed reindex can remove the prior retrieved content without version lineage. | Use a stable source identity/version and make replacement lifecycle auditable; add collision and failed-reindex tests. | No |
| BRV-RAG-004 | Medium | VERIFIED | `app/database/models.py:Chunk.heading_path`; `app/rag/retriever.py:Retrieved`, `citation` | Heading is stored on chunks but not selected into `Retrieved`; citation output uses UUID source ID and optional page/sheet/cell only. Source content hash/version is also unavailable. | Consumers cannot receive stored heading provenance or a stable content/version identifier needed to distinguish changed source evidence. | Preserve heading and source version/hash in retrieval/citation contracts; T8 checks frontend preservation. | No |
| BRV-PLAT-001 | High (conditional) | VERIFIED | `app/rag/retriever.py:retrieve`; `app/rag/rerank.py:llm_rerank` | Retrieved passage content, including the propagated department-scoped content above, is passed to LLM rerank with `sensitive=False`. | T6 egress finding applies directly to the T3 retrieval path. | Retain T6 ID; Sol decision and sensitive-rerank test remain required. | Yes |

## Parser, duplicate, and fallback evidence

| Area | Evidence | State |
|---|---|---|
| PDF/DOCX/XLSX/Markdown routing | `detect_kind` dispatches PDF text/table, Docling formats, and Markdown; PDF text uses pypdf fallback. | VERIFIED |
| Table citation accuracy | `_table_cell_range` returns a range only when the Docling item exposes anchors; otherwise it returns `None` rather than synthesizing a range. | VERIFIED conservative behavior; installed Docling/version output is `NEED FILE/CONTEXT` |
| Duplicate corpus payloads | `audit_data_layout` hashes manifest-active corpus files and treats active duplicate groups as audit errors. | VERIFIED boot audit for manifest corpus; it does not supply source versioning for API/CLI records |
| RRF/rerank fallback | RRF is deterministic; disabled rerank returns fused results; LLM rerank catches errors and returns original order. | VERIFIED |
| Manifest audit policy | Policy can report unmanifested files as warnings; CLI manifest-only mode performs the actual selection enforcement. | VERIFIED separation of audit and ingestion enforcement |

## Test evidence and command

| Evidence | State | Notes |
|---|---|---|
| `tests/test_bravo_data_audit.py` exercises manifest-only selection and active duplicate-hash audit. | Read only; not executed | Does not exercise `--allow-unmanifested` with no department or API upload metadata. |
| `tests/test_ingestion_wpa.py` covers parser dispatch, PDF page provenance, Markdown heading parsing, and optional Docling paths. | Read only; not executed | Docling assertions skip when unavailable; no source→chunk scope propagation test. |
| `tests/test_bravo_corpus_manifest.py` and `test_bravo_intent.py` cover manifest metadata and post-retrieval intent boost. | Read only; not executed | No metadata pre-filter assertion or citation heading/hash contract test. |
| `tests/test_egress_embedding.py` tests `sensitive=True` cloud refusal. | Read only; not executed | Does not prove source classification supplied to `ingest_source` is trustworthy. |
| Expected scoped command | `pytest -q tests/test_bravo_data_audit.py tests/test_ingestion_wpa.py tests/test_bravo_corpus_manifest.py tests/test_bravo_intent.py tests/test_egress_embedding.py` | Not run: host Python/pytest unavailable. |

## T3 exit check

- Source → manifest → parser → chunk → metadata → embed → retrieve flow is traced.
- BRV-API-002 is confirmed through source-to-chunk propagation and SQL retrieval scope.
- Required, optional, and derived metadata are separated; parser provenance availability is stated without assuming installed Docling behavior.
- No knowledge-graph decision or target architecture is made; no production code, config, migration, or test was changed.
