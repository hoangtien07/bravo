# P0-05 — Citation audit

Status: `COMPLETE FOR LIVE AUDIT SAMPLE — mixed VALID_FULL/VALID_PARTIAL/MISSING results`

Nhãn citation: `VALID_FULL`, `VALID_PARTIAL`, `IRRELEVANT`, `UNVERIFIABLE`, `FABRICATED`, `MISSING`.

| Test | Claim | Citation | Accessible | Support label | Notes |
|---|---|---|---|---|---|
| T03.1 P2 | Phiếu nhập mua không bắt buộc Đơn mua hàng; mục 8.4.3 | Bravo 10 – Phần 8 – Quản lý mua hàng (8.4.3) | Not checked | UNVERIFIABLE | Cần source/corpus fixture để xác minh |
| T01.1 P5 | Các bước lập Phiếu nhập mua; kho ảnh hưởng giá vốn; một phiếu một hóa đơn | Bravo 10 – Phần 8 – Quản lý mua hàng | Not checked | UNVERIFIABLE | Citation chỉ ở mức phần tài liệu |
| T01.4 P4 | Quy trình change/approval/rollback | NB_QT27K.01, NB_QT27K.04 | Not checked | UNVERIFIABLE | Không được dùng làm bằng chứng ISMS cho tới khi mở audit |
## Wave 2 rows

| T01.3 P1 | Candidate B30 table names are not confirmed as Phiếu nhập mua storage | No citation | N/A | MISSING | Correct abstention but no auditable schema source |
| T03.2 P2 | Phiếu nhập mua → Phân bổ chi phí mua hàng / Đề nghị thanh toán mua hàng | `Knowledge Graph - Bravo 10` | Not checked | UNVERIFIABLE | Broad label, no node/edge/page |
| T04.3 P3 | NB_QT99K.99 absent; NB_QT27K.09 section 5.1/page 3 says monthly backup at least one month | NB_QT27K.09 URL with `page=3` | Yes | VALID_FULL | Live viewer showed page 3/5 and the quoted retention sentence |
| T11.1 P4 | Least privilege and approval path for payroll schema | NB_QCATTT; NB_QT27K.05 | Not checked | UNVERIFIABLE | URLs appeared in answer; exact clauses pending |
## Wave 4–5 rows

| T04.4 | AutoMergeXSecureMode does not appear in Layout XML technical docs | None | N/A | MISSING | Safe no-result |
| T01.5 | Posting/closing/reconciliation precede financial reports | No claim-level URL in captured output | N/A | UNVERIFIABLE | Useful business linkage, audit required |
| T06.2/T06.3 | Graph edges and event IDs | user-guide-graph / user-guide-graph (e4_028 etc.) | Not checked | UNVERIFIABLE | Internal graph provenance, no public page |
| T11.2 | NB_QT.01 roles and sections 5.1.1.1–5.1.1.4 | NB_QT.01 page 3 URL | Yes | VALID_PARTIAL | Page 3 and document-control scope loaded; role sequence not on inspected page |
| T03.4 | Six-step domestic purchasing workflow | help.bravo.com.vn | Not checked | UNVERIFIABLE | Broad homepage citation |
| T12.1 | NB_QT27K.01 and NB_QT27K.15 change/data protection claims | Malformed/non-HTTP links | No | IRRELEVANT | Do not treat as evidence |

## Wave 6 rows

| T01.6 | Accounting close/posting/reconciliation prerequisites and account-class linkage | Chapter17_Accounting page 84 HTTPS URL | Yes | VALID_PARTIAL | Page 84 exists and is section 17.8, but visible page text does not prove the full generated sequence |
| T13.3 | End-to-end purchasing sequence | `knowledge_graph` | N/A | MISSING | Internal source label, no node/edge/page |
| T06.4 | Fabricated graph entity has no result | None | N/A | MISSING | Correct abstention; no citation expected |
| T05.2 | Payroll-SQL policy claims and citation correction | Replacement HTTPS URLs plus malformed prior IDs | Not checked | VALID_PARTIAL_PENDING | Self-audit correctly flags the prior malformed links; replacement pages still need opening |
| T13.4 | Context update preserves v10.2/SQL Server/goal and changes platform | None | N/A | MISSING | Behavioral memory observation, not a source claim |
