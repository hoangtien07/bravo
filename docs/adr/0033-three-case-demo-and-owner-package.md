# 0033. Khóa gói quyết định demo ba case và guardrail từ demo đến pilot

- **Trạng thái:** **Accepted** (2026-07-31) — chủ dự án xác nhận
  `CONFIRM ALL. OD-08 thêm 2 case nữa`.
- **Ngày:** 2026-07-31
- **Người quyết định:** Chủ dự án.
- **Căn cứ:** [Owner decision packet](../../plan-rebuild/11-OWNER-DECISION-PACKET-RECONCILIATION-DEMO.md)
  OD-01 đến OD-10.
- **Amends:** [ADR-0032](0032-first-v2-demonstrator-reconciliation-exception.md) ở phạm vi demo:
  giữ Bank Reconciliation là case primary/deep và bổ sung hai case functional/bounded.
- **Không supersede:** các invariant deterministic, RLS, no-free-form-SQL, draft-first,
  payload-bound maker-checker, evidence lineage và baseline-freeze gate.

## Bối cảnh

ADR-0032 đã chọn Reconciliation & Exception Investigator, subtype Bank statement ↔ sổ tiền gửi
BRAVO, làm demonstrator sâu đầu tiên. Để chuyển thiết kế thành kế hoạch có thể giao dev, còn phải
khóa đồng thời user/buyer, dữ liệu, model, deployment, egress, integration, packaging, phạm vi
frontend/backend, release gates và điều kiện promote sang pilot.

Chủ dự án xác nhận toàn bộ OD-01 đến OD-10 và yêu cầu OD-08 thêm hai case. Quyết định này cần được
ghi thành ADR mới vì ADR Accepted là bất biến; không sửa ngược nội dung lịch sử của ADR-0032.

## Quyết định

### 1. Ba case chức năng

Demo có một shared Accounting Work inbox và ba case dùng chung `AccountingCase`, versioned
evidence, review và trace contracts:

1. **Bank Reconciliation — primary/deep**
   - Bank statement ↔ sổ tiền gửi BRAVO;
   - deterministic normalization, matching, aggregation, tolerance và exception classification;
   - bounded LLM cho missing context, ambiguous mapping, explanation và investigation narrative.
2. **Voucher Evidence & Accounting Review — functional/bounded**
   - synthetic invoice, PO/contract, receipt/QC nếu áp dụng và BRAVO draft-voucher snapshot;
   - deterministic total, tax, duplicate, lineage và 3-way evidence checks;
   - LLM giải thích ambiguity và đề xuất mapping/treatment alternatives;
   - không tạo ledger hoặc tự post voucher.
3. **Period Close Readiness — functional/bounded**
   - synthetic period scope, prerequisite status, reconciliation reference và evidence gap;
   - deterministic dependency/completeness checks;
   - LLM hỏi dữ kiện thiếu và giải thích readiness/next action;
   - BRAVO vẫn sở hữu depreciation, costing, FX, closing entry, report và period lock.

Thứ tự bắt buộc: shared core → Bank Reconciliation qua deterministic gate → Voucher Review →
Period Close Readiness. Hai case bổ sung không được dùng làm lý do tạo platform abstraction mới
trước khi Bank Reconciliation hoạt động và được kiểm thử.

### 2. User, buyer và entitlement

- preparer: reconciliation/accounting user;
- checker: chief accountant hoặc reviewer được chỉ định;
- buyer hypothesis: chief accountant/controller;
- Knowledge Chat và Accounting Operations Hub có entitlement riêng trong cùng product shell;
- chưa xây billing UI và chưa tuyên bố price/WTP đã được xác thực.

### 3. Demo data, model và identity

- synthetic versioned fixtures only; không dữ liệu khách hàng;
- một pinned frontier cloud model/version cho demo và matched comparison;
- giữ trusted application auth/RLS shell;
- không Keycloak/OIDC trong demo;
- không production, on-prem hoặc offline-readiness claim từ demo.

### 4. Pilot target và real-data policy

- reference target: customer-managed single-tenant on-prem data plane trong private network;
- raw evidence, deterministic processing, audit và backup ở customer-side;
- cloud LLM chỉ nhận policy-approved minimized/redacted exception context;
- egress cần allowlist, audit, customer approval và DPA;
- private/local model là fallback khi khách hàng không cho egress, chưa được coi tương đương chất
  lượng trước khi qua cùng benchmark;
- trước dữ liệu thật phải có ADR supersede/amend ADR-0019 và ADR-0022.

### 5. Integration và mutation

- demo dùng versioned file fixtures;
- pilot API-first read-only với field/coverage audit;
- supported versioned BRAVO export là fallback;
- không direct DB hoặc arbitrary SQL;
- write integration tương lai chỉ là typed payload-bound draft sau maker-checker;
- không autonomous posting, payment, close/lock hoặc master-data mutation.

### 6. Release và promotion gates

Áp dụng toàn bộ OD-09 và OD-10:

- deterministic monetary/match exactness 100% trên frozen golden set;
- zero critical false negative trên critical held-out set;
- zero scope leak, unsafe mutation và approval bypass;
- exact claim có source/rule lineage;
- prerequisite/scope recall ≥90%, correction fidelity ≥95%;
- Core V2 thắng ≥60% non-tied blind comparisons với current Consultant;
- reviewer completion time giảm ≥30% khi có manual baseline;
- ≥80% accepted recommendations không cần material accounting edit;
- không promote sang paid pilot nếu thiếu discovery, design partner, connector coverage,
  identity/egress/DPA, recovery, update/rollback, support hoặc real-data ADR.

## Không thuộc phạm vi

- automatic voucher/journal posting;
- live bank connectivity;
- BRAVO transaction/close/report engine;
- generic Task/Kanban/Gantt;
- Management Variance hoặc case thứ tư;
- full Governance Console, billing, marketplace, Agent Catalog hoặc agent builder;
- multi-tenant SaaS, unrestricted multi-agent hoặc arbitrary SQL.

## Hệ quả

### Tích cực

- dev có một shared core và ba ví dụ đủ rộng để chứng minh product direction;
- Bank Reconciliation vẫn là case chuẩn để bảo vệ độ sâu và causal evaluation;
- hai case bổ sung chứng minh khả năng tái sử dụng contract mà không làm lại BRAVO;
- toàn bộ quyết định lớn được khóa trong một lần, giảm decision churn khi implementation.

### Chi phí và kiểm soát scope

- effort tăng so với một case; vì vậy hai case sau bắt buộc reuse core và triển khai tuần tự;
- mỗi case cần deterministic policy, fixtures, must-not claims và acceptance tests riêng;
- `Ready for Dev` vẫn có điều kiện: runtime containment và A/B baseline freeze phải hoàn tất trước
  mọi thay đổi prompt/routing/retrieval/synthesis;
- quyết định topology/model cho pilot là target architecture, không phải production-readiness
  evidence.
