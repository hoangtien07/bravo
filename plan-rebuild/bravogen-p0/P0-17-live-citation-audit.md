# P0-17 — Live citation audit

Audit date: 2026-07-15. Read-only browser inspection of URLs emitted by BravoGen; no credentials, uploads or mutations.

| Citation | Accessible | What was observed | Support verdict |
|---|---|---|---|
| `NB_QT27K.09 ... page=3` | Yes | Viewer loaded page 3/5. Section 5.1 visibly states daily/weekly backup cadence and “Bản sao lưu hàng tháng được lưu trữ ít nhất 01 tháng.” | `VALID_FULL` for the quoted retention claim; does not validate the rejected fake code beyond the no-result response |
| `Chapter17_Accounting&page=84` | Yes | Viewer loaded page 84/90 and displayed the heading `17.8. Kế toán tổng hợp`; visible page text did not contain the full close/posting sequence captured in T01.6. | `VALID_PARTIAL` (document/page exists; claim-level support incomplete) |
| `NB_QT.01 ... page=3` | Yes | Viewer loaded page 3/12 and displayed purpose/scope/definitions for document and record control. | `VALID_PARTIAL` for document-control scope; role sequence cited by T11.2 requires later pages/sections |

## Interpretation

BravoGen can emit a directly navigable source URL and the source viewer can expose page content. Citation quality is therefore not uniformly fabricated, but claim-level support varies: exact page/section claims can be verified, while broad document labels or a page containing only a section heading are insufficient evidence for all generated procedural detail.

This audit does not establish how URLs are generated, whether every citation is retrieved for the current answer, or whether the visible viewer is the same retrieval source used by the model.
