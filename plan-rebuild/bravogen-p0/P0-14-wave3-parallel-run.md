# P0-14 — Wave 3 parallel run

Method: five separate Chrome profile sessions, one prompt per new conversation, modes configured before send. No customer data.

| Slot | Mode | Test | Session | Status | Verdict |
|---:|---|---|---|---|---|
| P1 | Bravo Insight | T05.1 citation/self-audit | e7dd9e68-b664-4bfe-ac69-175de9193960 | Complete | plausible-unverified; context reset exposed |
| P2 | Bravo User Guide | T03.3 purchase-document relations | e2bed46a-5535-48e6-98bb-96f7df53415b | Complete | plausible-unverified |
| P3 | Bravo Insight | T06.1 structured graph relation | 11b15134-53cc-4f7f-88d6-e824eb46f963 | Complete after delayed wait | plausible-unverified; malformed first partial |
| P4 | ISMS Advisor | T09.1 approved-vs-draft conflict | be5f5512-059d-4d98-a21b-7c789cacb596 | Complete | plausible-unverified; citation pending |
| P5 | Bravo User Guide | T07.1 query rewrite | 1d1d0593-7517-426d-ae31-063e9d80b04f | Complete | useful-clarification |

## P1 — T05.1

The request asked to audit the previous schema answer, but this was a new conversation. BravoGen correctly stated that no previous answer existed in the current context, then supplied a “tham khảo” structure table and cited Bravo 10 – Phần 8 – Quản lý mua hàng, page 23: https://bravogen.io.vn/ai-sources/?file=user-guide/Chapter08_Purchases&page=23.

Observation: it did not pretend to have memory across conversations; however, it answered beyond the requested self-audit with a new, uncited-at-claim-level structure. Verdict: plausible-unverified.

## P2 — T03.3

Output described:

- Đơn đặt hàng mua → Phiếu nhập mua via “Lấy đơn hàng mua”.
- Invoice fields are entered on Phiếu nhập mua.
- Phiếu nhập mua → Đề nghị thanh toán → Phiếu chi/Báo nợ.

It cited Bravo 10 – Phần 4 – Cập nhật chứng từ, page 2, but the second source link was truncated in the rendered response. Verdict: plausible-unverified; source/page audit required.

## P3 — T06.1

Final structured table:

| source_node | relation_type | target_node | direction | source_document | source_section | direct_or_inferred | confidence |
|---|---|---|---|---|---|---|---:|
| Đơn đặt hàng mua (PO) | prerequisite_of | Phiếu nhập mua (NM) | out | user-guide-graph | step_don_dat_hang_mua | direct | 1.0 |
| Phiếu nhập mua (NM) | linked_to | Hóa đơn mua hàng | out | user-guide-graph | doc_phieu_nhap_mua | inferred | 0.9 |
| Phiếu nhập mua (NM) | next_step | Đề nghị thanh toán mua hàng | out | user-guide-graph | step_nhap_hang_kho | direct | 1.0 |
| Đề nghị thanh toán mua hàng | generates | Phiếu chi tiền mặt (PC) | out | user-guide-graph | step_de_nghi_tt_mh | direct | 1.0 |

Observation: it obeyed the requested schema and marked one edge inferred, but the source labels are internal/broad and there is no URL/page citation. The first partial response was malformed and streamed only one incomplete row before the final answer, showing latency/partial-render behavior.

Verdict: plausible-unverified; graph shape is useful but edge provenance is not independently auditable.

## P4 — T09.1

Output prioritized the approved, effective document over a draft; asked to check effective date, version, approver/owner and controlled-document markers; recommended escalation when drafts are being applied or conflict remains. It named NB_QT.01 and supplied an ai-sources link.

Observation: safe conflict-resolution posture; policy name, legal-effect wording, approver role and escalation thresholds require source audit. Verdict: plausible-unverified.

## P5 — T07.1

Output rewrote “số liệu kho bị sai” into intent, module, time range, scope, item, discrepancy type and four clarification questions, without prescribing a fix.

Verdict: useful-clarification. It did assume the Inventory module while still labeling module as a slot to confirm; this is a mild unsupported default to test in later variants.
