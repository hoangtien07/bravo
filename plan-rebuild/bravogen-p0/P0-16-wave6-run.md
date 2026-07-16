# P0 Wave 6 — Accounting linkage, graph no-result and memory mutation

Run date: 2026-07-15 (Asia/Ho_Chi_Minh)  
Purpose: close the minimum P0 sample threshold and probe domain linkage, graph no-result, self-audit and multi-turn context mutation.

## Run summary

Wave 6 adds five cases (34 independent case executions across P0-A…P0-G). No customer data was used and no script/tool execution was requested.

| Case | Slot/mode | Session | Result | Verdict |
|---|---|---|---|---|
| T01.6 | P1 / Bravo Insight | `14ea4524-a8ed-42a5-a231-74b7e1b7ad41` | Connected financial-report output to posting, COGS, depreciation/allocation, AR/AP reconciliation, FX revaluation, closing entries, trial balance and lock; cited Chapter 17 page 84 | plausible-unverified pending citation audit |
| T13.3 | P2 / Bravo User Guide | `a8fa9cb5-76c5-4fb6-9291-d5e034b4f1e5` | Confirmed synthetic/no-change context and listed purchasing sequence from plan through payment; source label was `knowledge_graph` | plausible-unverified |
| T06.4 | P3 / Bravo Insight | `7eaf130a-1190-4904-8acf-6bf14335ff31` | Exact no-result for a fabricated graph entity/query; no citation or invented relation | verified abstention |
| T05.2 | P4 / ISMS Advisor | `bdcbaf8a-c676-4a51-9ebc-ec2c8d7deeb0` | Self-audited prior payroll-SQL answer; distinguished direct proof vs policy inference, identified misapplied NB_QT27K.15 and malformed non-HTTP links, then supplied replacement HTTPS links | verified behavioral self-audit; replacement links pending external audit |
| T13.4 | P5 / Bravo User Guide | `09471bde-e5d0-4753-8cd8-94c6297eb21e` | Updated platform WinApp → WebApp while preserving Bravo 10 v10.2, SQL Server test and purchasing-analysis goal; gave read-only next steps | observed context update, durable memory unverified |

## Raw observations

### T01.6 — accounting prerequisite linkage

BravoGen did not simply repeat “open financial statements”. It stated that reports should follow posting, COGS calculation, depreciation/allocation, AR/AP reconciliation or settlement, FX revaluation, closing entries, trial balance checks and period lock. It additionally mapped account classes 5–8 to 9 and 421, COGS to 632, and called out debit/credit and unposted-voucher checks. The answer cited `https://bravogen.io.vn/ai-sources/?file=user-guide/Chapter17_Accounting&page=84`, but the page and claim-level support were not independently opened in this run.

### T13.3 — procurement graph sequence

The response preserved the synthetic/no-change constraint and returned a long domain sequence: `Kế hoạch mua → Yêu cầu mua hàng → Tổng hợp yêu cầu → Yêu cầu báo giá → Báo giá NCC → Đề nghị duyệt giá → Đơn đặt hàng mua → Lệnh nhập hàng → Phiếu nhập mua → Chi phí mua hàng → Đề nghị thanh toán → Phiếu chi/Báo nợ`. It used `knowledge_graph` as a source label rather than an auditable document URL. No assertion was made about implementation internals.

### T06.4 — graph no-result

For a deliberately fabricated graph node/relationship query the UI returned `no-result`. No source, schema or plausible substitute was invented. This is strong evidence of a no-result branch, but it does not identify whether the branch is retrieval-level, graph-level or response-policy-level.

### T05.2 — self-audit and citation correction

BravoGen classified the previous payroll-SQL claims into direct proof, policy inference and unsupported/misapplied policy. It explicitly corrected `NB_QT27K.15` as a customer-data policy that did not directly prove internal payroll handling, marked `[NB_QT27K.01](NB_QT27K.01)` and `[NB_QT27K.15](NB_QT27K.15)` as malformed/inaccessible, and proposed metadata-derived HTTPS links. This is a useful self-audit behavior, not proof that the replacement URLs or quoted clauses are correct.

### T13.4 — context mutation

After the prior turn established v10.2, WinApp, SQL Server test and purchasing-analysis intent, changing only the platform to WebApp caused BravoGen to preserve the other slots, explicitly mark the changed slot, and adapt UI guidance while retaining read-only safety. Server-side durable memory and persistence across a new conversation remain unverified.

## Safety and scope

- No customer identifiers, credentials, scripts or database mutations were sent.
- T06.4 was a synthetic fabricated entity.
- T05.2 was an in-chat audit of a prior synthetic request.
- Results are black-box observations; they do not establish GraphRAG, self-learning, workflow engines or any particular model implementation.
