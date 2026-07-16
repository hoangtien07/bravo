# P0-01 — Test matrix

## Batch P0-A — Mode boundary

| Test | Nội dung | Chạy trên |
|---|---|---|
| T01 | Domain routing: User Guide, XML, schema, ISMS, HR | Cả 3 mode |
| T02 | Cùng một câu hỏi quan hệ chứng từ | Cả 3 mode |
| T20 | Cross-domain leakage | Cả 3 mode |

## Batch P0-B — Retrieval và hallucination

| Test | Nội dung | Trọng tâm |
|---|---|---|
| T03 | Retrieval dependence | yêu cầu bằng chứng trực tiếp, no-general-knowledge |
| T04 | Fabricated entities | XML, field, process code, voucher, version giả |
| T08 | Ambiguity handling | câu hỏi làm rõ có giá trị chẩn đoán |
| T15 | Refusal quality | chống ép đoán, nêu dữ kiện thiếu và bước tiếp theo |
| T17 | Tool/retrieval failure behavior | phân biệt no-result, failure, no-permission, invalid query |

## Batch P0-C — Citation

| Test | Nội dung |
|---|---|
| T05 | Citation validity và self-audit |
| T16 | Claim-level evidence, direct/inferred |
| T19 | Confidence calibration |

## Batch P0-D — Knowledge Graph

| Test | Nội dung |
|---|---|
| T06 | node/edge/direction/provenance/traversal/reverse/stability |
| T07 | query rewriting và query expansion |

## Batch P0-E — Version và conflict

| Test | Nội dung |
|---|---|
| T09 | conflict resolution, status/effective date/scope |
| T10 | Bravo 8/10/unspecified/plausible-fake version |

## Batch P0-F — Security và context

| Test | Nội dung |
|---|---|
| T11 | permission behavior bằng tình huống giả lập |
| T12 | instruction trong retrieved data, không lấy bí mật |
| T13 | coreference, topic shift, correction, stop/continue |

## Batch P0-G — Stability

| Test | Nội dung |
|---|---|
| T14 | repeated runs, new sessions, cross-mode stability |
| T18 | template theo procedure/definition/troubleshooting/comparison |

## Execution order

1. P0-A trước để xác nhận bề mặt ba mode.
2. P0-B ngay sau đó để đo failure/hallucination quan trọng nhất.
3. Chỉ audit citation đã xuất hiện thật.
4. Chỉ gọi hành vi graph là graph-like cho đến khi T06 có bằng chứng ổn định.
5. P0-F dùng tình huống giả lập, không yêu cầu dữ liệu nhạy cảm thật.

## Run-control fields

Mỗi lượt phải có `test_id`, `variant_id`, `mode`, `session_id`, `run_number`, timestamp, prompt hash, raw output, citations, claims, classification và scores.
