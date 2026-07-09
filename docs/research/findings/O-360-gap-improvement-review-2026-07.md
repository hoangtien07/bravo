# Findings O — 360 Gap & Improvement Review

> Ngày quét: 2026-07-09. Mục tiêu: phản biện 360 sau Findings L/M/N để tìm các hướng cải thiện khác, hạn chế/lỗi/điểm mù còn lại của BRAVO AI Copilot. Nguồn: mixed evidence, ưu tiên 2024-2026, phân hạng độ tin cậy; không dùng Sci-Hub, không dùng cookie/session ResearchGate.

## 1. TL;DR

Lượt này không đảo các invariant lõi đã chốt: **RLS trước context, no free SQL, LLM không tự tính số, constrained workflow, HITL/draft, eval trước mở rộng**. Nhưng có 9 điểm mù 360 có thể ảnh hưởng roadmap 90 ngày tới:

1. **Rủi ro lớn nhất vẫn là không có bằng chứng mua thật.** Web research không thay được 8-12 phỏng vấn CFO/kế toán trưởng/IT manager BRAVO; mọi dữ liệu giá VN/MISA/Bizzi vẫn mù. Quyết định: `ADD_RESEARCH` bằng primary interview, không quét web thêm.
2. **AI adoption fail vì thiếu workflow integration và strategic clarity, không phải thiếu model.** Các báo cáo/case 2025-2026 đều lặp: công cụ AI chỉ tạo ROI khi gắn vào workflow, owner, metric, training/champion và cost visibility. Quyết định: `CHANGE` pilot design.
3. **Cost visibility là enterprise gate.** KPMG 2026 nêu nhiều tổ chức thiếu visibility chi phí AI; BRAVO on-prem càng cần unit economics/cost-to-serve per-site, không chỉ inference cost. Quyết định: `ADD_EVAL`.
4. **On-prem/air-gap là moat nhưng cũng là nợ vận hành.** Nguồn mới củng cố cảnh báo: self-host LLM có upgrade, GPU, security default, support offline, model drift, talent cost. Quyết định: `CHANGE` sales claim: chỉ bán "sovereignty-ready" sau sovereignty spike.
5. **KB/version drift là lỗi sản phẩm độc lập với hallucination.** VersionRAG cho thấy naive RAG chỉ 58-64% accuracy với câu hỏi version-sensitive; BRAVO có user guide/KQPT/PTNV nhiều phiên bản nên cần version-aware metadata. Quyết định: `CHANGE`.
6. **Accounting rule artifact cần được quản trị như model/risk artifact.** SR 11-7 và NIST AI RMF củng cố: mapping_rules, TT99 crosswalk, VAT/TSCĐ rules cần purpose, owner, validation, version, effective date, independent review. Quyết định: `CHANGE`.
7. **Competitor moat erosion đến từ platform control plane, không chỉ tính năng AP.** SAP/Salesforce đang bán agent lifecycle, builder, guardrails, governance, low-code, data integration. BRAVO không nên build full platform, nhưng cần minimal workflow cards/control plane cho nội bộ. Quyết định: `ADD_EVAL/CHANGE`.
8. **Agent security gap chuyển từ RAG sang tool/permission/admin.** OWASP LLM06 nhấn mạnh excessive functionality/permissions/autonomy; BRAVO đã đúng hướng but cần tool inventory, least privilege, on-behalf-of identity, rate-limit, monitoring. Quyết định: `KEEP + CHANGE`.
9. **Observability/eval không chỉ cho dev, mà là điều kiện trust.** OpenTelemetry GenAI conventions và Salesforce/SAP product pages cho thấy lifecycle supervision/monitoring đã thành table stakes. Quyết định: `CHANGE`.

## 2. What We Already Know / Do Not Re-Research

| topic | status | lý do |
|---|---|---|
| Generic secure/permission-aware RAG | CLOSED | Findings M đủ bằng chứng; chỉ eval nội bộ thêm |
| Generic hybrid retrieval/rerank | CLOSED as research | Chuyển sang ablation nội bộ |
| No free-form SQL | CLOSED | EntSQL/Spider2 và repo ADR đủ để KEEP |
| Spreadsheet agents | CLOSED | SpreadsheetBench 2 đủ để DEFER automation |
| Multi-agent write/autonomous finance | CLOSED | Không có evidence production-grade; giữ constrained workflow |
| Agent end-user workflow patterns | CLOSED as broad research | Findings N đủ; tiếp theo là pilot nội bộ |
| AP vendor job list | CLOSED as broad research | Findings L đủ; dữ liệu còn thiếu là giá thật/primary interviews |

## 3. New 360 Gap Matrix

| track | gap | evidence | repo/current-doc impact | decision | priority | next action |
|---|---|---|---|---|---|---|
| Product/WTP | Giá và willingness-to-pay VN vẫn mù | Repo nhiều lần ghi 0 giá VN; web search không ra giá MISA/Bizzi tin cậy | `MONEY-ENGINE-ROADMAP`, `ROADMAP` | ADD_RESEARCH | P0 | 8-12 interview + mystery-shopping MISA/Bizzi |
| Pilot/adoption | Pilot hiện thiên về demo năng lực hơn học hành vi mua/dùng | MIT/BCG/Ramp signals: value cần workflow integration, strategy, learning; M365 Copilot qualitative trial mixed | `ROADMAP`, `MATURITY-LADDER` | CHANGE | P0 | Pilot protocol before/after + champion + time/correction metrics |
| Cost/unit economics | On-prem margin/cost-to-serve chưa đo | KPMG AI cost visibility; on-prem ops sources; repo đã cảnh báo sovereignty-ảo | `RUNBOOK-PACKAGING`, `MONEY-ENGINE-ROADMAP` | ADD_EVAL | P0 | Cost model per-site: GPU, install, update, support, backup, training |
| On-prem/air-gap ops | Moat chủ quyền chưa thành năng lực vận hành | On-prem challenge sources + self-host LLM exposure study | `DEPLOY-DEMO`, `RUNBOOK-DR`, ADR-0009 | CHANGE | P0 | Sovereignty spike + secure-by-default offline checklist |
| ERP closed-loop | Export Excel đủ pilot nhưng chưa đủ commercial lock-in | Findings L + SAP/Salesforce platform integration pages | ADR-0016, `COUNCIL-REVIEW` | KEEP+ADD_RESEARCH | P1 | Excel as control feature; ERP API owner/deadline as commercial roadmap |
| Accounting governance | Rules/crosswalk có thể sai hệ thống mà verify-gate số không bắt | SR 11-7 model risk; repo council nêu TSCĐ/VAT issues | `app/accounting`, ADR-0012 | CHANGE | P0 | Versioned rule artifact + accountant sign-off + rule test set |
| Security/identity | SSO/admin already better in docs, nhưng tool least-privilege/control plane cần rõ | OWASP LLM06; Salesforce/SAP governance claims | `app/agent/tools.py`, `SECURITY-RLS` | CHANGE | P0 | Tool inventory, permissions, on-behalf-of, agent scope tests |
| KB lifecycle | Version drift/stale docs chưa thành first-class risk | VersionRAG, doc management/RAG sources | `BRAVO-KB-TAXONOMY-EVAL` | CHANGE | P0 | source version/effective date/owner/freshness SLA |
| Observability | OTel/metrics có thể có nền nhưng thiếu GenAI-specific spans/eval ops | OTel GenAI semconv, Salesforce lifecycle supervision | `app/observability`, eval docs | ADD_EVAL | P1 | Trace per retrieval/tool/LLM/eval; incident taxonomy |
| Competitive moat | Low-code agent builders/control planes làm generic capability dễ bị copy | SAP Joule, Salesforce Agentforce | `BRAVO-AI-GAP-USP-MAP` | CHANGE | P1 | Moat shift: BRAVO schema/rules/data governance, not "has agent" |
| Scope discipline | Project dễ quay lại bẫy nhiều agent/ít user | Council + MIT/BCG adoption evidence | `MONEY-ENGINE-ROADMAP` | KEEP/STOP | P0 | Maturity gate: no new agent until 1 real user + pilot metric |

## 4. Evidence Matrix

| source_id | title/vendor | type | claim | evidence_quality | what it warns/improves | BRAVO relevance | recommended action |
|---|---|---|---|---|---|---|---|
| O1 | [MIT GenAI Divide coverage](https://www.tomshardware.com/tech-industry/artificial-intelligence/95-percent-of-generative-ai-implementations-in-enterprise-have-no-measurable-impact-on-p-and-l-says-mit-flawed-integration-key-reason-why-ai-projects-underperform) | report coverage | Most GenAI pilots lack measurable P&L impact; integration gap is key | MEDIUM | Tool access without workflow learning fails | BRAVO must measure pilot value, not model demos | CHANGE pilot protocol |
| O2 | [BCG/Ramp synthesis via Business Insider](https://www.businessinsider.com/ai-adoption-strategies-companies-2026-7) | press synthesis of reports | Strategy/clarity and high-intensity adoption outperform mere tool access | MEDIUM | Adoption needs complementary org change | Pilot needs champions, training, clear use of saved time | CHANGE adoption plan |
| O3 | [M365 Copilot qualitative trial](https://arxiv.org/abs/2503.17661) | arXiv empirical | Six-month trial produced mixed outcomes; workflow integration, privacy, oversight matter | MEDIUM | Broad copilots disappoint without context/deep workflow | Avoid generic chat as main value proof | ADD_EVAL user cohort |
| O4 | [M365 Copilot usage at enterprise scale](https://arxiv.org/abs/2605.23958) | arXiv production-data | Work usage spans writing, retrieval, analysis, but uneven across jobs | MEDIUM-HIGH | Adoption patterns differ by role | Evaluate support/kế toán/BA separately | ADD_EVAL cohort metrics |
| O5 | [KPMG AI cost visibility coverage](https://www.techradar.com/pro/were-seeing-a-clear-divide-many-business-leaders-admit-they-only-have-a-limited-understanding-of-ai-budgets) | survey coverage | Cost visibility and leadership accountability correlate with ROI | MEDIUM | AI budget opacity kills ROI | On-prem needs full cost-to-serve model | ADD_EVAL cost model |
| O6 | [Running on-premise in an agentic world](https://www.techradar.com/pro/running-on-premise-in-an-agentic-world) | industry analysis | Self-hosting brings maintenance, talent, upgrade and hardware refresh costs | LOW-MED | On-prem can become stale/expensive | Do not sell sovereignty as cheap/easy | CHANGE sales claim |
| O7 | [Self-hosted LLM deployments in the wild](https://arxiv.org/abs/2505.02502) | arXiv empirical | Public LLM deployments often expose insecure endpoints/auth/configs | MEDIUM | Secure-by-default operations matter | Air-gap/offline does not excuse hardening | CHANGE deployment checklist |
| O8 | [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) | official framework | AI risk management spans design, development, use and evaluation; GenAI profile released | HIGH | AI governance must be lifecycle-based | BRAVO needs AI risk register + lifecycle controls | CHANGE governance docs |
| O9 | [Federal Reserve SR 11-7](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm) | official supervisory guidance | Model risk requires purpose, validation, ongoing monitoring, effective challenge, inventory | HIGH | Finance models/rules need independent challenge | Treat mapping_rules/crosswalk as controlled artifacts | CHANGE accounting governance |
| O10 | [OWASP LLM06 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) | official security guidance | Risks stem from excessive functionality, permissions, autonomy; mitigate via least privilege/HITL/complete mediation | HIGH | Tool scope is security boundary | Build tool inventory + on-behalf-of permissions | CHANGE security |
| O11 | [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) | official observability spec | GenAI spans/metrics/events exist as standardization area | HIGH | LLM/tool/retrieval observability becoming standard | Add trace attributes for retrieval/tool/LLM/eval | ADD_EVAL observability |
| O12 | [VersionRAG](https://arxiv.org/abs/2510.08109) | arXiv benchmark | Version-sensitive QA fails under naive RAG; version-aware retrieval improves accuracy | MEDIUM | Stale/old docs cause wrong-but-sourced answers | BRAVO KQPT/PTNV/user guide need effective date/version | CHANGE KB lifecycle |
| O13 | [Enterprise metadata-enriched RAG](https://arxiv.org/abs/2512.05411) | arXiv | Metadata enrichment improves retrieval quality | MEDIUM | Metadata is not optional for enterprise KB | Add source_type, owner, module, version, scope metadata | CHANGE ingestion/eval |
| O14 | [Invoice Information Extraction evaluation](https://arxiv.org/abs/2510.15727) | arXiv | Invoice extraction should be evaluated field-by-field and consistency checks | MEDIUM | AP parser quality is field-specific | AP eval must use field exact match + consistency failures | ADD_EVAL AP parser |
| O15 | [Electronic invoice audit bot](https://arxiv.org/abs/2402.04517) | case study/preprint | E-invoice automation worked when humans only verified exceptions | MEDIUM | Good human-robot task choice matters | BRAVO AP should route exceptions, not force full autonomy | KEEP+CHANGE |
| O16 | [SAP Joule page](https://www.sap.com/products/artificial-intelligence.html) | official product docs | SAP positions AI via unified workspace, agents, business data, governance, process context | MEDIUM | Competitive moat moves to embedded workflow/context | BRAVO moat must be BRAVO schema/rule expertise | CHANGE positioning |
| O17 | [Salesforce Agentforce](https://www.salesforce.com/agentforce/) | official product docs | Agent lifecycle includes build/test/deploy/manage/orchestrate, guardrails, data protection | MEDIUM | Platform control plane is table stakes for large vendors | BRAVO needs minimal workflow cards, not full platform | ADD_EVAL |
| O18 | [FlowAgent](https://arxiv.org/abs/2502.14345) | arXiv | Workflow agents need compliance plus out-of-workflow handling | MEDIUM | Pure prompt autonomy violates procedural compliance | Encode BRAVO workflow cards with OOW/clarify states | ADD_EVAL |
| O19 | [Agentic AI industry barriers](https://arxiv.org/abs/2605.14675) | arXiv interview study | Production integration blocked by verification gap, confidentiality, non-determinism, proprietary context | MEDIUM | HITL remains trusted verifier | BRAVO constrained/eval-first stance is correct | KEEP |
| O20 | [AI-assisted coding maintenance burden](https://arxiv.org/abs/2510.10165) | arXiv empirical | AI productivity can shift rework burden to experts | MEDIUM | Faster draft generation may overload senior reviewers | Track reviewer load for accounting/support pilots | ADD_EVAL |

## 5. Decision Backlog

| decision | priority | repo/product impact | action |
|---|---|---|---|
| CHANGE | P0 | Pilot design | Convert AP+TT99 pilot from demo to measured before/after workflow with champion users |
| ADD_RESEARCH | P0 | GTM/pricing | Replace web research with 8-12 primary interviews + MISA/Bizzi mystery-shopping |
| CHANGE | P0 | Accounting domain | Make `mapping_rules`/TT99 crosswalk/VAT/TSCĐ rules versioned, sourced, accountant-approved artifacts |
| CHANGE | P0 | KB lifecycle | Add `effective_date`, `version`, `owner`, `supersedes`, `approved_status` to KB metadata and retrieval filters |
| CHANGE | P0 | Security/tooling | Build tool/action inventory with least privilege, on-behalf-of identity, high-impact HITL |
| ADD_EVAL | P0 | On-prem economics | Build per-site cost-to-serve model and sovereignty spike evidence |
| CHANGE | P1 | Observability | Add GenAI traces/events for retrieval, rerank, tool call, LLM call, verify gate, approval |
| ADD_EVAL | P1 | Workflow architecture | Introduce workflow cards registry for AP/support/implementation, with OOW/clarify states |
| KEEP | P1 | ERP closed-loop | Excel/CSV is acceptable pilot control feature; ERP write-back remains commercial roadmap |
| STOP | P0 | Scope | No AR/Anomaly/Tax/IFRS expansion until one real user and AP/support pilot metrics |

## 6. Top 10 Improvements

1. **Primary WTP sprint:** interview 8-12 BRAVO CFO/kế toán trưởng/IT manager; target >=3 conditional LOI or explicit no-buy reasons. Benefit: kills pricing fantasy early. Not over-engineering: no code.
2. **Pilot protocol v1:** define baseline, intervention, metrics, user cohorts, data boundaries for AP+TT99 and Support Copilot. Benefit: converts demo into evidence. Not over-engineering: measurement wrapper.
3. **Rule artifact governance:** versioned mapping/rules with source citation, effective date, owner, accountant sign-off, change log. Benefit: prevents correct-looking wrong accounting. Not over-engineering: replaces hard-coded ambiguity.
4. **KB version-aware retrieval:** filter by approved/effective version and warn on stale/superseded docs. Benefit: prevents wrong-but-sourced answers. Not over-engineering: metadata + retrieval rule, not new RAG architecture.
5. **Correction/review burden metrics:** track edit diff, correction reason, reviewer time, senior reviewer load. Benefit: detects AI shifting work to experts. Not over-engineering: pilot telemetry.
6. **Tool inventory and least-privilege map:** every tool has owner, permissions, data scope, write risk, HITL requirement. Benefit: satisfies OWASP LLM06-style controls. Not over-engineering: table/config before platform.
7. **Sovereignty spike:** run one local model path with network blocked, measure latency/VRAM/quality and document egress endpoints. Benefit: turns moat into evidence. Not over-engineering: one spike, not infra rewrite.
8. **Cost-to-serve sheet:** include GPU, install, update, offline support, backup, monitoring, training, customer success. Benefit: prevents false margin. Not over-engineering: spreadsheet/markdown model.
9. **GenAI observability minimal standard:** trace retrieval/tool/LLM/verify/approval with run ID and hard-fail tags. Benefit: supports debugging and trust. Not over-engineering: aligns with existing audit/eval.
10. **Workflow cards registry:** define job-to-be-done, inputs, outputs, allowed tools, OOW handling, owner, metrics for 3 workflows only. Benefit: controlled evolution toward agent platform. Not over-engineering: limited to AP/support/implementation.

## 7. Top 10 Stop/Defer

| item | decision | reopen trigger |
|---|---|---|
| New finance agents beyond AP+TT99 | STOP | AP/support pilot has real users + measured value |
| Full low-code agent builder | STOP | >=5 internal workflows demand non-engineer configuration |
| Agent marketplace/MCP ecosystem expansion | DEFER | Real customer asks for connectors beyond BRAVO docs/AP |
| Outcome pricing with air-gap telemetry | DEFER | Signed offline metering/audit design accepted by customer |
| ERP write-back as pilot blocker | STOP | Pilot proves Excel bottleneck blocks adoption |
| Tax/IFRS prose assistant for sales demo | STOP | Corpus + claim/citation gate + accountant/legal review complete |
| On-prem "cheaper than cloud" sales claim | STOP | Cost-to-serve model proves it for target customer tier |
| Generic chatbot as main product positioning | STOP | Only if support pilot shows broad chat has measurable ticket deflection |
| Long-horizon autonomous workflow | STOP | pass^k/state eval and HITL checkpoints meet hard gates |
| More broad web research on VN pricing | STOP | Replace with calls/mystery-shopping; web has hit diminishing returns |

## 8. Pilot Experiments

| experiment | dataset/users | metric | pass/fail threshold | owner area |
|---|---|---|---|---|
| AP+TT99 before/after | 50-100 real XML invoices, 2-3 accountants | minutes/invoice, % approved-without-edit, correction taxonomy, hard fail | >=30% time reduction, >=70% approved/no major edit, 0 hard fail | product/accounting/eval |
| Rule governance validation | TT99 crosswalk + VAT/TSCĐ cases | rule exactness, source coverage, accountant sign-off | 100% rules have source/effective date/owner; no unsigned rule in demo | accounting/product |
| Support/Implementation Copilot | 50 real support/implementation questions | citation correctness, draft reuse, first-response time, escalation reduction | citation >=95%, draft reuse >=40%, hallucinated procedure = 0 | KB/RAG/support |
| Version-aware KB retrieval | 30 version-sensitive KQPT/user guide questions | correct version hit rate | >=90% uses approved/effective version; stale warning on old docs | ingestion/RAG |
| Sovereignty spike | 5 smoke workflows on local model with network blocked | egress count, latency, VRAM, quality | 0 egress; documented p95 and failure cases | platform/ops |
| Cost-to-serve model | 2 deployment tiers | per-site margin sensitivity | show breakeven at conservative usage/support assumptions | product/finance |
| Tool least-privilege eval | all tools/actions | excessive permissions, unauthorized action attempts | 0 unauthorized tool action; all write-like tools require HITL | security/agent |
| Reviewer burden eval | pilot correction logs | reviewer minutes/case, senior review load | no hidden increase in senior reviewer workload > baseline | product/eval |
| Observability drill | 20 failed/successful trajectories | trace completeness and debug time | >=95% runs trace retrieval->tool->verify->approval; failure root cause findable | platform/eval |

## 9. ADR/Docs That May Need Updates

| doc | update |
|---|---|
| `docs/ROADMAP.md` | Add WTP primary interview and measured pilot gates before new agent expansion |
| `docs/MONEY-ENGINE-ROADMAP.md` | Clarify TT99 as wedge, not recurring engine; add cost-to-serve and rule-governance gates |
| `docs/BRAVO-KB-TAXONOMY-EVAL.md` | Add version/effective-date/owner/approved-status metadata and stale-doc tests |
| `docs/SECURITY-RLS.md` | Add tool inventory, on-behalf-of identity, complete mediation, high-impact HITL |
| `docs/RUNBOOK-PACKAGING.md` | Add air-gap update/install/support model and cost-to-serve assumptions |
| `docs/RUNBOOK-DR.md` | Add restore drill as pilot readiness evidence |
| `docs/adr/0012-verify-gate-number-integrity.md` | Extend or supersede with claim/rule/citation verification and rule artifact governance |
| `docs/adr/0018-agentic-packaging-knowledge-as-data.md` | Add workflow cards/control-plane-lite and versioned rule/config governance |

## 10. Research Ledger

### Queries used

- `enterprise AI pilot failure workflow integration ROI`
- `AI copilot adoption change management field study enterprise`
- `on premise generative AI deployment operations air gapped update support`
- `accounts payable automation benchmark cost per invoice touchless rate 2025`
- `ERP AI copilot case study production SAP Oracle Microsoft finance`
- `AI agent observability evaluation production incident`
- `AI governance audit trail financial services model risk generative AI`
- `Vietnam enterprise SaaS AI pricing willingness to pay`
- `self hosted AI assistant enterprise security SSO audit logging`
- `knowledge base freshness RAG stale documents enterprise`

### Closed for now

- Generic secure RAG.
- Generic hybrid retrieval/rerank.
- General NL2SQL safety.
- Spreadsheet agent autonomy.
- Broad agent end-user case studies.
- AP vendor job taxonomy.

### Requires primary customer interview, not more web research

- MISA/Bizzi/Agentwork real pricing in Vietnam.
- CFO willingness-to-pay for TT99/AP assistant.
- Whether Excel import is accepted as control feature or seen as incomplete ROI.
- Which BRAVO role feels the most pain first: kế toán, support, triển khai, BA/PTNV.
- Required legal/SLA wording for AI-created accounting drafts.

### Requires reasoning xtra-high

1. Whether to keep AP+TT99 as single commercial wedge or split effort with Support/Implementation Copilot.
2. Whether Excel/CSV should be framed as pilot-only workaround or as deliberate audit-control feature.
3. How to classify mapping/rule artifacts: code, data, model, or controlled accounting policy.
4. How far to go on workflow cards before it becomes a platform-building trap.
5. Whether on-prem is sold as default, premium regulated option, or proof-of-sovereignty capability.

## Bottom Line

The main new improvement direction is **not another agent**. It is turning BRAVO from a technically promising demo into a measured, governed, buyer-believable pilot:

1. Primary WTP research.
2. Rule/KB governance.
3. Version-aware knowledge lifecycle.
4. Tool/control-plane-lite.
5. Cost/sovereignty evidence.
6. Observability and pilot metrics.

If these are not done, the project can be right technically and still fail commercially or operationally.
