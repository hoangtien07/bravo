# FigmaMake standalone Accounting Intelligence completion plan

**Status:** `READY FOR DEV HANDOFF` — owner direction accepted; commit this decision set, then
start with WP20-00 inventory/retention freeze. No release or production-readiness claim.

**Decision date:** 2026-08-18

**Consolidated:** 2026-08-19

**Repository baseline inspected:** `9ae8192`

**Authority:** ADR-0035, Plan 19/ADR-0034 for Conversation V2 contracts, and ADR-0032/0033 for the
three bounded accounting cases, as amended below.

**Canonical frontend:** `FigmaMake_UI`

**Product boundary:** BRAVO Accounting Intelligence is a standalone analysis and review product. It
does not call a BRAVO API, connect to a live BRAVO database, automate the BRAVO UI, post vouchers,
update ledgers, run closing, lock periods or execute any accounting mutation in BRAVO.

The Figma UI may call this project's own authenticated API. Users may manually upload files or
reports exported from BRAVO and other systems. Those files are evidence inputs, not a live ERP
connection.

Plan 19 and Plan 20 are complementary, not competing product plans:

- Plan 19 owns the framework-independent intelligence pipeline: lossless `TaskUnit`
  decomposition, evidence planning, deterministic read-only work products, claims, verification,
  rendering and evaluation.
- Plan 20 owns the shipped product boundary, FigmaMake information architecture, file/evidence
  intake, accounting-case delivery order, Artifact Workspace and retirement of ERP-like surfaces.
- In the current product, Plan 20/ADR-0035 supersede Plan 19 wording about a `draft proposal`,
  write tool, draft builder or future ERP mutation. Those terms mean a read-only analysis proposal
  only. A future BRAVO connector or mutation requires a new owner ADR and is not latent scope.

## 1. Owner decision and outcome

From this plan onward:

1. Product development happens on `FigmaMake_UI`; `frontend-react` is legacy and must not remain the
   production build target.
2. BRAVO remains the system of record. Any operation that should occur once in BRAVO stays in BRAVO.
3. This product reads user-supplied evidence, performs deterministic checks and assisted reasoning,
   manages findings/review, and exports review reports.
4. The product must not produce a button, lifecycle state or file that implies it posted, closed,
   locked, reconciled or otherwise changed BRAVO.
5. Suggested accounting treatment is permitted as analysis. A suggested debit/credit entry is not
   an executable journal, not an import-ready BRAVO payload and not proof that posting occurred.
6. New accounting capabilities are admitted only when they are useful as independent analysis over
   uploaded evidence and have frozen contracts, fixtures, rules and SME acceptance.
7. Office output is an **Artifact Workspace capability after verified analysis**, not a separate
   Office Agent and not a general-purpose document automation product in this scope.

Target product modules:

- **Knowledge Chat** — grounded BRAVO/accounting guidance and structured accounting analysis.
- **Accounting Work** — evidence-driven deterministic cases and findings.
- **Knowledge & Rules** — governed manuals, policies, account/tax rules and source lifecycle.
- **Administration & Audit** — users, permissions, retention, feedback and reconstructable traces.

There is no ERP Integration module in the current product.

## 2. Current-state findings

### 2.1 What is already aligned

- Figma live routes already center on Knowledge Chat, conversation history and `/work`.
- AccountingCase V2 already has bounded Bank Reconciliation, Voucher Evidence Review and Period
  Close Readiness cases.
- Current case screens explicitly state that review artifacts do not post, close or lock BRAVO.
- Authorization, RLS, evidence snapshots, deterministic checks, findings and audit foundations are
  reusable.
- Current bank/voucher/period-close engines can be retained if their inputs are changed from
  synthetic fixtures to governed file-derived evidence without adding BRAVO connectivity.

### 2.2 What conflicts with the new direction

| Area | Current evidence | Decision |
|---|---|---|
| Production frontend | `Dockerfile` builds and serves `frontend-react`, not `FigmaMake_UI` | Cut production build and SPA serving to FigmaMake; freeze/archive the legacy UI. |
| Legacy mutation metaphor | `create_journal_entry`, journal draft queue, approval and manual ERP-import export remain active | Remove from product/API/tool registry. Preserve historical data read-only until a retention migration is approved. |
| ERP integration option | `app/erp/client.py`, connector catalog and comments retain future BRAVO API/DB integration | Remove from active dependency graph and documentation. Any future integration requires a new owner ADR. |
| Duplicate tool pages | Money Engine, generic Anomaly, Tax and Knowledge Graph remain in prototype/QA inventories | Remove from production and QA navigation. Re-admit only as governed Accounting Work cases. |
| Ambiguous lifecycle | UI/types include `approved`, `externally_executed`, `executed`, `verified` | Replace with analysis/review states that cannot be confused with ERP execution. |
| Import-ready accounting output | `journal_export.py` creates CSV/XLSX for manual ERP entry | Retire. Export only human-readable review reports and neutral data extracts, not BRAVO import files. |
| Synthetic-only work | AccountingCase API is still gated as a synthetic demonstrator | Add governed upload/normalization adapters and real user-owned evidence snapshots. |
| Duplicate chat paths | `/ask`, `/agent/ask` and `/chat/{id}/messages` coexist | FigmaMake uses one Conversation V2 endpoint; retire duplicates after compatibility audit. |
| Product language | API title and old design docs describe an ERP/copilot/integration product | Rename active copy to standalone Accounting Intelligence; retain historical documents as archives. |

### 2.3 No destructive deletion first

Removing a feature from the product does not immediately authorize dropping its database tables or
deleting user artifacts. First remove reachability, disable creation and export, provide any required
read-only retention view, then perform a separately reviewed data migration.

### 2.4 Honest adjudication of the 2026-08-19 review

The attached review is directionally strong, but several statements are hypotheses rather than
current evidence. The plan adopts only the changes with a large expected effect:

| Review statement | Adjudication used by this plan |
|---|---|
| Put Office after verified accounting analysis | **Adopt.** It prevents a renderer or editing model from becoming accounting truth. |
| Use templates/brand packs, surgical edits and structural plus visual QA | **Adopt.** These are durable enterprise document controls. |
| Benchmark Office engines before selection | **Adopt.** Current repository/readme claims do not prove BRAVO round-trip fidelity. |
| OfficeCLI is the leading engine | **Not decided.** It is one benchmark candidate; rapid release activity and feature claims are not fidelity evidence. |
| Open XML SDK is the production foundation | **Not decided.** It is a strong structural/surgical candidate, but its low-level API creates implementation cost and does not itself provide rendering fidelity. |
| Voucher Review should become the flagship | **Not accepted as product truth.** Bank Reconciliation remains the ADR-selected first deep vertical slice. Voucher Review is a high-value discovery candidate, not a validated buyer/WTP decision. |
| Transaction Analysis has little moat | **Treat as a product hypothesis.** It remains a mandatory Knowledge Chat quality anchor and deterministic work product, but is not a separate hero navigation module. |
| WP19 is complete | **Incorrect if stated broadly.** WP19-00 frozen A/B capture and owner fixture acceptance are recorded; independent SME review, Core V2 implementation and blind quality gates remain open. |
| Plan 20 has already removed BRAVO connectivity/mutation | **Boundary decision only.** Current code still registers legacy routes/tools and still ships `frontend-react`; WP20-01/02 must remove reachability and prove it with negative tests. |
| Use 10 real files per Office format | **Narrow.** Start with a small, legally approved, sanitized representative corpus (target 5–10 per format). No customer or confidential file enters the benchmark without explicit authority. |

This adjudication preserves the useful product direction without converting technology enthusiasm,
market intuition or a completed baseline capture into implementation evidence.

## 3. Final product information architecture

### 3.1 Production routes

| Route | Surface | Priority |
|---|---|---|
| `/` | New Knowledge Chat | P0 |
| `/c/:conversationId` | Active conversation and structured work product | P0 |
| `/conversations` | Conversation history | P0 |
| `/shared/:token` | Explicitly shared, read-only conversation/report | P1 |
| `/work` | Accounting Work inbox | P0 |
| `/work/new/:caseType` | Create an evidence-driven case | P0 |
| `/work/cases/:caseId` | Scope, evidence, checks, findings and review | P0 |
| `/work/cases/:caseId/findings/:findingId` | Finding investigation | P0 |
| `/imports` | Upload packs, mapping, validation and lineage | P0 |
| `/knowledge` | Governed sources and rules | P1 |
| `/artifacts` | Artifact Workspace: review reports, governed native Office files and neutral extracts | P1 |
| `/admin` | Users, permissions, retention, audit and quality feedback | P1 |

Temporary redirects may remain for `/accounting-work` and `/financial-close`, but they must not
present separate duplicate modules.

`/review?qa=1` remains a development-only design/evaluation route and must not be included in the
production bundle or navigation.

### 3.2 Routes removed from the product

- `/approvals`
- `/tools/money-engine`
- `/tools/anomaly`
- `/tools/tax`
- `/tools/knowledge-graph`
- separate legacy Financial Close graph/readiness surfaces outside Accounting Work

Useful logic from these surfaces may be extracted into later Accounting Work engines; their legacy
routes, fixtures and lifecycle language are not retained as product features.

### 3.3 Navigation

The production navigation contains only:

1. Knowledge Chat
2. Hội thoại
3. Công việc kế toán
4. Nhập dữ liệu
5. Kho tri thức & quy tắc
6. Báo cáo phân tích
7. Quản trị, only when authorized

Do not expose provider selection, frontier capabilities, engineering workbench, schema/KEDB tools,
prototype fixtures or feature flags to ordinary accounting users.

## 4. Allowed and forbidden product actions

### 4.1 Allowed

- Upload, parse, validate, map, version and retain user-owned evidence.
- Search governed manuals/policies and answer with claim-level citations.
- Calculate bounded accounting values using approved deterministic rules.
- Compare evidence sources, reconcile rows, classify exceptions and explain findings.
- Suggest accounting treatment, missing evidence and next review steps.
- Assign a finding, comment, request more evidence and record a review disposition.
- Export a PDF/XLSX/DOCX/PPTX review artifact or neutral CSV result table that clearly identifies
  its source, rule version and non-execution status.
- Edit a product-generated or explicitly approved-template artifact only through a declared edit
  scope, previewed diff and versioned save; semantic accounting values remain read-only.
- Preserve a reconstructable audit trace within this product.

### 4.2 Forbidden

- Calling a BRAVO REST/SOAP/API endpoint or reading a live BRAVO SQL database.
- Browser/computer automation against BRAVO.
- Creating or posting a BRAVO voucher or journal.
- Updating a ledger, account balance, master record, tax record or document status.
- Running allocation, depreciation, costing, closing, reporting or period locking in BRAVO.
- Generating BRAVO-specific import SQL/XML/CSV intended to execute the suggested entry.
- Marking a case as executed, posted, closed, locked or reconciled merely because analysis passed.
- Treating an uploaded export as current unless its cutoff/version/coverage is verified.
- Letting an Office renderer or editing model alter verified accounting values, evidence links,
  review decisions, sensitivity/retention metadata or locked brand elements.
- General arbitrary editing of user-uploaded Office files before the Office fidelity and
  permission gates in section 6.4 pass.

### 4.3 Replacement lifecycle

Replace the legacy draft/approval/execution lifecycle with:

```text
new
  -> evidence_pending
  -> evidence_ready
  -> checked
  -> needs_review
  -> changes_requested | reviewed | accepted_exception | escalated
  -> artifact_ready
  -> archived
```

Use `evidence_verified` only for evidence integrity/authority. Never use a bare `verified` status that
could be interpreted as confirmation in BRAVO.

Maker/checker separation remains useful for internal review of high-risk findings and reports. It
must be named `prepared_by` / `reviewed_by`, not approval to execute an ERP action.

## 5. Data intake without BRAVO API

Every Accounting Work case starts from a versioned import pack.

| Capability | Minimum input pack | Validation before analysis |
|---|---|---|
| Bank Reconciliation | Bank statement CSV/XLSX/MT940 where approved; BRAVO bank-ledger export CSV/XLSX | account/currency/period, opening/closing control totals, row uniqueness, cutoff, schema mapping |
| Voucher Evidence Review | Invoice XML/PDF; PO/contract; receipt/QC; voucher report/snapshot exported from BRAVO; applicable policy | document identity, supplier, amount/tax totals, dates, duplicate keys, evidence completeness and source version |
| Period Close Readiness | Close checklist; trial balance/report exports; subledger reconciliation reports; approval evidence; policy pack | entity/ledger/period, cutoff/freshness, prerequisite applicability, reconciliation references and coverage |
| Accounting Transaction Analysis | User scenario or spreadsheet; selected account/tax policy | currency/scale, VAT basis, policy version, assumptions and balanced expected postings |
| Future AP/AR review | Aging/open-item exports and supporting settlement documents | control totals, as-of date, counterparty identity, open/cleared status and duplicate keys |

Import workflow:

1. Upload to product-owned object storage.
2. Malware/type/size check.
3. Parse to a staging preview; never silently coerce failed values.
4. User confirms column mapping and scope.
5. Validate control totals, freshness and required fields.
6. Create an immutable evidence snapshot with checksum and lineage.
7. Run deterministic analysis only when the case-specific coverage rule passes.
8. Supersede rather than overwrite a prior snapshot.

No input adapter may require a BRAVO credential, hostname, connection string or session.

## 6. Capability portfolio

### 6.1 P0 completion capabilities

#### A. Knowledge Chat V2

- Lossless task decomposition, especially multi-item accounting prompts.
- Governed retrieval with version/authority/citation checks.
- Structured `AnswerPlan`, claim/calculation lineage and a shared verifier.
- Multi-turn corrections and explicit assumptions.
- Attachment/import-pack references without treating document text as instructions.
- No mutation tools in the chat tool inventory.

#### B. Accounting Transaction Analysis

This closes the demonstrated ten-transaction gap without creating a journal-posting feature.

- Debit/credit treatment by selected accounting policy.
- VAT inclusive/exclusive calculation using `Decimal`.
- Payment split and remaining payable/receivable.
- Required assumptions and alternative policy handling.
- Balanced, read-only work product with calculation lineage.
- Output label: `Phân tích đề xuất — chưa ghi nhận trong BRAVO`.
- Export only a review worksheet/report, not a BRAVO import template.

#### C. Bank Reconciliation & Exception Investigation

- File mapping and control totals.
- Exact/compound/timing/unmatched classifications.
- Coverage and stale-evidence handling.
- Finding review, comments, disposition and evidence-backed explanation.
- Review artifact and neutral exception table.

#### D. Voucher Evidence Review

- Invoice/PO or contract/receipt or QC/voucher snapshot matching.
- Tax, duplicate and account/dimension policy checks where governed.
- Missing/conflicting/stale evidence findings.
- Suggested correction description only; no voucher creation or post.

#### E. Period Close Readiness

- Applicable prerequisite inventory.
- Evidence freshness and coverage.
- References to completed reconciliations and review decisions.
- Ready/not-ready/abstained result with reason codes.
- No close, lock, allocation, report-run or posting action.

#### F. Review, Artifact Workspace and audit foundation

- Finding assignment, comment, request-evidence and disposition.
- Immutable evidence/result/review hashes.
- PDF/XLSX/DOCX human-readable artifacts and neutral CSV result export. PPTX is P1 unless the
  accepted use case and fidelity benchmark promote it.
- RLS, audit, retention and read-only sharing.

### 6.2 P1 necessary supporting capabilities

- Import Center and reusable mapping profiles.
- Knowledge/Rule administration with owner, version, effective date and supersession.
- Chart-of-accounts and tax-policy selection for analysis.
- Artifact Workspace, Brand/Template Registry and saved report templates.
- Notifications/inbox for assigned findings and evidence requests.
- Admin views for users, capabilities, retention, usage, feedback and quality incidents.
- Evaluation console for frozen test cases and SME grading; not visible to ordinary users.

### 6.3 P2 expansion candidates

These replace, rather than reactivate, the generic legacy Anomaly/Tax/Money pages. Each requires a
separate frozen fixture and SME decision:

1. Accounts Payable open-item and aging review
2. Accounts Receivable open-item and collection review
3. General-ledger anomaly review from uploaded ledger export
4. Fixed-asset roll-forward and depreciation-evidence review
5. VAT/tax reconciliation from uploaded declarations and ledger reports
6. Financial-statement variance and mapping review

P2 capabilities remain absent from production navigation until their data contracts, rules,
critical false-negative bounds and blind SME gates pass.

### 6.4 Enterprise Artifact Workspace direction

The Office direction follows the high-value patterns used by frontier enterprise productivity
platforms without copying their product surface:

| Frontier pattern | BRAVO contract |
|---|---|
| Work on native, editable documents | Produce valid OOXML artifacts that remain editable in Word, Excel and PowerPoint; do not rasterize the primary deliverable. |
| Ground generation in authorized enterprise sources | Artifact content may use only verified analysis results, approved evidence refs and sources visible under the current RLS context. |
| Plan before a complex generation/edit | Create an `ArtifactPlan`/`ArtifactEditPlan` with format, audience, sections/sheets/slides, source set, template and edit scope; the user reviews material changes before save. |
| Keep the human in control | Show preview, intended diff, warnings and version history; support reject, revise and restore. “Generated” never means “reviewed”. |
| Use native application primitives | Prefer Word styles/sections, Excel tables/formulas/charts and PowerPoint masters/layouts/placeholders rather than drawing everything as positioned shapes or images. |
| Govern brand centrally | `BrandRegistry` and `TemplateRegistry` version fonts, colors, logos, masters and reusable components; locked zones cannot be changed by the model. |
| Respect enterprise policy | Propagate owner, classification, retention, sharing policy and audit references to the artifact record; engine/provider use is capability- and policy-gated. |
| Preserve sources and feedback | Store source/evidence references, renderer/template versions, validation results and user review feedback with the artifact trace. |

The semantic pipeline is:

```text
VerifiedAnalysisResult
    -> ArtifactPlan
    -> BrandedArtifactSpec
    -> ArtifactEnginePort
    -> RenderedArtifact
    -> StructuralValidation
    -> NativeRender/VisualValidation
    -> HumanReview
    -> versioned ArtifactStore
```

Minimum contracts:

- `VerifiedAnalysisResult`: immutable semantic values, findings, evidence/rule lineage and review
  state accepted as input to rendering;
- `ArtifactPlan`: artifact kind, audience, purpose, source result IDs, template/version and required
  sections/sheets/slides;
- `BrandedArtifactSpec`: component-level content bound to approved templates and locked zones;
- `ArtifactEditPlan`: target artifact/version, allowed components, requested semantic-neutral edit,
  expected diff and approval requirement;
- `ArtifactDiff`: actual package/component changes with an allowlist verdict;
- `RenderedArtifact`: file hash, MIME type, renderer/version, source hashes and supersession link;
- `ArtifactValidationReport`: structural, formula/data-integrity, visual, compatibility and policy
  results;
- `ArtifactEnginePort`: provider-neutral create/edit/render interface. Domain and accounting engines
  do not import OfficeCLI, Open XML SDK, ONLYOFFICE or a commercial SDK.

V1 is intentionally case-bound:

1. Bank Reconciliation: `Bank_Reconciliation_Review.xlsx` with Summary, Matched, Exceptions,
   Bank-only, BRAVO-only, Review and Source Metadata sheets.
2. Voucher Evidence Review: `Voucher_Review_Report.docx` with scope, evidence, checks, findings,
   unresolved issues, reviewer and source hashes.
3. Cross-case management summary PPTX is P1 after its decision audience, template and source rules
   are frozen. It does not block the Bank or Voucher exits.

V1 does not accept “upload any Word/Excel/PowerPoint and let AI edit it.” Template-safe edits are
limited to product-generated artifacts and explicitly approved templates. Broader editing is P2
and requires separate retention, permission, macro/external-link, embedded-object and data-loss
controls.

#### 6.4.1 Engine decision: benchmark first

| Candidate | Allowed role before benchmark exit |
|---|---|
| OfficeCLI | R&D adapter and rapid create/edit/render candidate only; no default-engine claim. |
| Open XML SDK | Structural inspection, validation and surgical OOXML adapter candidate; not an agent-facing API and not automatically the renderer. |
| ONLYOFFICE | Optional future human browser editor after licensing/deployment review; not a required runtime dependency. |
| Commercial Office SDK | Benchmark challenger when open-source candidates miss required fidelity or support thresholds. |
| Microsoft Office/LibreOffice native render | Compatibility/visual oracle where licensing and controlled automation permit; not a server-side product dependency by default. |

Select engines per format if that reduces risk; XLSX, DOCX and PPTX do not have to share one
implementation. Before a format ships, use an approved, sanitized corpus targeting 5–10
representative files for that format. The benchmark must include:

- no-op open/save round trip with package and visual diff;
- surgical edit where only declared components may change;
- XLSX formulas, cached values, number/conditional formats, named ranges, charts, print settings,
  hidden sheets, external links and formula-injection defenses;
- PPTX theme/master/layout, placeholders, footer, notes, charts, grouped shapes, image crop and
  embedded objects;
- DOCX styles, sections, headers/footers, tables, page breaks, numbering, TOC, captions, fields and
  tracked changes;
- opening/rendering in the approved native compatibility matrix.

Required engine exit: 100% structural validity on the corpus, zero undeclared semantic/formula
changes, zero locked-brand changes, every intended edit represented in the diff, no critical visual
overflow/corruption, acceptable deterministic performance, supported licensing and an operable
offline path. If no candidate passes, narrow the artifact feature or buy a supported engine; do not
hide fidelity defects with screenshots.

## 7. API allowlist and decommission plan

### 7.1 Production API families retained

- authentication and authorized administration;
- conversations, messages, attachments, sharing and feedback;
- governed knowledge sources;
- imports and evidence snapshots;
- AccountingCase list/create/read/check/review/artifact endpoints;
- artifacts and audit-safe run status/events.

### 7.2 Retire from the production router

| Current route/module | Action |
|---|---|
| `routes_invoices` / `/invoices/draft` | Remove; invoice parsing becomes an evidence adapter, not journal creation. |
| `routes_drafts` / `/drafts*` | Disable new use; migrate relevant records to analysis artifacts; remove journal export. |
| `routes_connectors` / `/connectors` | Remove; no BRAVO connector catalog in this product. |
| `routes_agents` generic anomaly/tax endpoints | Remove; later rebuild behind typed AccountingCase APIs. |
| `routes_graph` generic knowledge graph | Remove from product API unless a measured retrieval use case is accepted. |
| `/ask` and `/agent/ask` | Deprecate after FigmaMake is fully on Conversation V2. |
| Consultant schema/KEDB/frontier endpoints | Keep internal/admin only if still required; never expose as accounting-user modules. |

### 7.3 Remove from active runtime dependency graph

- `app.erp.client`
- ERP connector registry/adapters
- `create_journal_entry` and `preview_journal_entry` agent tools
- `app.erp.draft_queue` for new journal activity
- `app.accounting.journal_export`
- computer-use proposals targeting ERP
- configuration fields whose only purpose is BRAVO API/DB connectivity

The useful journal calculation primitives may be refactored into the read-only Transaction Analysis
engine. They must no longer construct a `DraftAction` or import-ready output.

## 8. FigmaMake production cutover

### 8.1 One frontend

- Build `FigmaMake_UI` in the Docker frontend stage.
- Serve `FigmaMake_UI/dist` from FastAPI with same-origin `/api` in production.
- Update SPA fallback and static-asset rules for Figma's root base.
- Update `README.md`, `README-DEV.md`, Compose, runtime evidence scripts and CI to use FigmaMake.
- Stop building, serving and documenting `frontend-react`.
- Move `frontend-react` to an explicit archive or delete it only after route/visual parity evidence and
  owner sign-off.

### 8.2 Remove prototype/live divergence

- `NormalRoutes` is the single source of production routes.
- Delete or isolate the old `AppShell`, `PrototypePages`, `OperationalToolPage`, legacy close graph,
  draft approval and generic tool fixtures from production imports.
- QA stories cover the same components/contracts as production; they do not maintain a second fake
  product with extra features.
- Remove `MONEY`, `ANOM`, `TAX`, `KGRAPH`, legacy `DRAFT` and duplicate `CLOSE` families from the
  production-completion matrix. Add Import, Transaction Analysis, Evidence, Finding and Artifact
  families.

### 8.3 Terminology rewrite

Use:

- `Công việc kế toán`, not `Công việc AI` as the primary navigation label;
- `Phân tích đề xuất`, not `bút toán nháp chờ ghi`;
- `Rà soát`, not `phê duyệt để thực thi`;
- `Xuất báo cáo phân tích`, not `xuất để nhập ERP`;
- `Nguồn BRAVO do người dùng tải lên`, not `kết nối BRAVO`;
- `Không thay đổi dữ liệu BRAVO`, shown once in context/help, not repeated noisily in every card.

## 9. Core and schema changes

### 9.1 AccountingCase contract amendment

- Replace `DraftAction` with `AnalysisArtifactPlan` containing report type, findings, evidence refs,
  neutral export schema, content hash and an explicit non-execution classification. This is the
  case-domain request to create an artifact; it does not duplicate the Artifact Workspace's
  renderer-level `ArtifactPlan`.
- Replace `ApprovalEnvelope` with `ReviewEnvelope` containing preparer/reviewer, evidence/result/
  decision hashes, review status and review timestamp.
- Remove execution-oriented target capability and payload fields.
- Rename source type `bravo_draft_voucher` to a neutral evidence term such as
  `bravo_voucher_snapshot` with explicit document status metadata.
- Retain immutable state transitions, revision checks, idempotency and maker/reviewer separation.
- Add a one-way binding from verified case result hash to `VerifiedAnalysisResult`; rendering and
  template-safe edits cannot write back into case truth.

### 9.2 Conversation Core V2

Continue Plan 19, with these amendments:

- no write tools or draft-to-ERP branch;
- Transaction Analysis is a read-only work-product engine;
- evidence comes from governed knowledge and uploaded snapshots;
- final answers link to cases/findings/artifacts in this product only;
- every adapter is provider/ERP independent and retains an offline-capable path.
- replace `draft proposal`, `draft action` and write-tool vocabulary with `analysis proposal`,
  `review request` and `artifact plan` in active Conversation V2 contracts and fixtures.

### 9.3 Persistence

- Add import packs, mappings, file objects, evidence snapshots and lineage.
- Add analysis artifacts and review envelopes.
- Add brand/template versions, artifact plans/specs/diffs, rendered-artifact versions and validation
  reports without storing duplicate authoritative accounting values.
- Preserve historical draft/journal rows read-only until retention/export obligations are resolved.
- A migration may tombstone obsolete route capability grants, but it must not erase user data in the
  same release.

## 10. Work packages

### WP20-00 — Freeze decision and product inventory

**Deliverables**

- ADR-0035 accepted for the FigmaMake-only, standalone/no-BRAVO-connectivity and bounded Artifact
  Workspace boundary.
- Machine-readable keep/rename/remove/defer inventory for UI routes, API routes, tools, config,
  schemas and tables.
- Frozen screenshots/API inventory and rollback commit.

**Exit**

- No ambiguous feature remains unclassified; retention owner approves the treatment of historical
  draft/journal records.
- The implementation baseline is a committed clean worktree with baseline commit and Alembic source
  head recorded. A live database head is recorded only when actually probed.

### WP20-01 — FigmaMake production cutover

**Deliverables**

- Docker, FastAPI SPA hosting, Compose, CI and documentation build FigmaMake only.
- Production route smoke tests, deep links, auth, SSE, responsive and accessibility tests.
- Legacy frontend no longer ships.

**Exit**

- A fresh production image serves the same FigmaMake UI tested in development; no runtime reference
  loads `frontend-react/dist`.

### WP20-02 — Product/API containment

**Deliverables**

- Production API allowlist from section 7.
- Removed legacy UI routes/navigation and disabled retired API families.
- Removed mutation/ERP tools from the chat inventory.
- Negative tests for every forbidden capability.

**Exit**

- Automated tests prove there is no callable path for BRAVO API/DB, computer use, journal creation,
  journal import export, posting, closing or locking.

### WP20-03 — Import Center and evidence adapters

**Deliverables**

- Upload, parsing, mapping preview, validation, versioning and lineage UI/API.
- Only the Bank statement, BRAVO bank export, voucher snapshot, invoice XML and the minimum
  period-close/transaction-analysis inputs required by the accepted fixtures. Add adapters only
  when an admitted case requires them.
- Failure states for invalid schema, missing control total, stale cutoff, conflict and supersession.
- No universal spreadsheet/PDF mapping DSL, connector catalog or generic import platform.

**Exit**

- Each P0 case can be created from a user-owned file pack without synthetic server fixtures or a
  BRAVO credential.

### WP20-04 — Conversation V2 and Transaction Analysis

**Deliverables**

- Plan 19 TaskUnit/EvidencePlan/AccountingWorkProduct/Claim/AnswerPlan/verifier contracts.
- Deterministic VAT, settlement and balanced accounting analysis.
- Ten-transaction golden case rendered in FigmaMake with task coverage, calculations, assumptions
  and citations.

**Exit**

- Before engine work starts, the existing owner-accepted fixture receives the independent
  accounting/BRAVO SME review still open in WP19-01.
- The ten-item anchor returns 10/10 analyzed units and exact independently reviewed values; no ERP
  draft, import file or mutation is created.

### WP20-05 — File-backed Accounting Work vertical slices

**WP20-05A — Bank Reconciliation, primary/deep**

- Upload → mapping → immutable evidence → deterministic matching → findings → review → artifact.
- Run the XLSX Office fidelity benchmark and select an engine only for the passing scope.
- Produce `Bank_Reconciliation_Review.xlsx` through `ArtifactEnginePort`, with structural, formula,
  visual and policy validation.

**WP20-05B — Voucher Evidence Review, functional/bounded**

- Reuse the same evidence/finding/review/artifact contracts; add only invoice/voucher/document
  identity, three-way evidence and governed policy checks.
- Run the DOCX fidelity benchmark before shipping `Voucher_Review_Report.docx`.

**WP20-05C — Period Close Readiness, functional/bounded**

- Start only after Bank and Voucher gates. Reuse uploaded evidence and reviewed reconciliation
  references; fail closed on missing coverage/freshness.
- Do not add a PPTX dependency or a new close engine to pass this slice.

Shared deliverables: findings, investigation, comments, dispositions, revised
`AnalysisArtifactPlan`/`ReviewEnvelope`, artifact source binding and immutable review trace.

**Exit**

- Each slice passes before the next begins. All three cases pass frozen deterministic fixtures plus
  held-out SME patterns; every conclusion has evidence/rule lineage and precise abstention when
  coverage is insufficient.
- Artifact validation proves the Office layer did not change verified semantic values. A failed
  Office benchmark narrows or defers that format; it does not block the accounting result/report
  fallback.

### WP20-06 — Knowledge, rules, Artifact Workspace and administration

**Deliverables**

- Knowledge source/version/effective-date management.
- Account/tax/rule-set governance.
- Brand/Template Registry, Artifact Workspace, assignment inbox, notifications and read-only
  sharing.
- Template-safe edit plan, preview/diff, locked elements, version restore and audit for generated or
  explicitly approved-template artifacts.
- PPTX management summary only after its audience/template/source contract and PPTX fidelity gate
  are accepted; it remains P1.
- Admin, audit, retention, feedback and quality incident screens.

**Exit**

- Every P0 result can be traced to input checksum, mapping, rule version, evidence refs, reviewer and
  artifact hash under RLS.
- Every Office change is attributable to an actor/request, input version, allowed edit scope,
  renderer/template version, actual diff and validation result.

### WP20-07 — Quality, security and offline gates

**Deliverables**

- Conversation and Accounting Work scorecards remain separate.
- Blind SME review, pass^k, RLS, injection, malformed-file, formula-injection, export and retention
  tests.
- Format-specific no-op/surgical/compatibility benchmarks, semantic-diff checks and locked-brand
  tests for every shipped Office adapter.
- Offline/local and approved cloud ablations with no change to deterministic/authorization gates.
- Desktop/tablet/mobile visual and accessibility matrix for production routes only.

**Exit**

- Zero critical accounting, leakage or forbidden-action failure; agreed quality/latency gates pass;
  owner signs the release packet.

### WP20-08 — Decommission and cleanup

**Deliverables**

- Remove retired code after retention and compatibility windows close.
- Remove obsolete capability grants/configuration and clean historical build/QA references.
- Archive superseded frontend/design documents with an explicit non-canonical label.

**Exit**

- Static dependency audit shows no active import or production route for retired ERP/draft surfaces;
  backup/restore and rollback drills pass.

## 11. Implementation order

```text
WP20-00 owner inventory
  -> WP20-01 FigmaMake production cutover
  -> WP20-02 product/API containment
      -> WP20-03 Import Center
          -> WP20-04 Conversation + Transaction Analysis
              -> WP20-05A Bank + governed XLSX artifact
                  -> WP20-05B Voucher + governed DOCX artifact
                      -> WP20-05C Period Close Readiness
                          -> WP20-06 supporting product + Artifact Workspace surfaces
                              -> WP20-07 release gates
                                  -> WP20-08 destructive cleanup after retention approval
```

WP20-01 and the non-destructive part of WP20-02 may run in parallel after the inventory is frozen.
WP20-04 and WP20-05 may share import/evidence contracts but must retain separate quality scorecards.
WP20-05A/B/C are sequential hard gates. Office engine work begins only after the verified semantic
result and the relevant format benchmark contract are frozen.

## 12. Test and acceptance matrix

| Gate | Required result |
|---|---|
| Canonical UI | Production image serves FigmaMake; no production build or documentation points to `frontend-react`. |
| No BRAVO dependency | Product boots and all P0 cases run with no BRAVO hostname, credential, API, database or browser session. |
| No duplicate mutation | No UI/API/tool can create/post/import a journal, run close, lock period or update BRAVO. |
| Route containment | Retired UI routes redirect safely or 404; retired API endpoints are absent/410 according to the compatibility decision. |
| Upload safety | Malformed, oversized, malicious, formula-injection and wrong-scope files fail safely before analysis/export. |
| Accounting exactness | 100% on critical deterministic fixture values; all suggested posting groups balance. |
| Evidence coverage | Exact claims and findings have approved evidence/rule lineage or are withheld. |
| Case behavior | Missing/stale/conflicting evidence yields precise findings/abstention, never a false ready/clean result. |
| Artifact semantic integrity | Renderer/editing cannot change verified values, findings, evidence refs or review decisions; every actual diff is allowlisted and audited. |
| Office fidelity | Each shipped format passes its approved no-op, surgical-edit, native-compatibility and visual corpus with zero critical corruption or locked-brand change. |
| Office governance | Artifact source scope follows RLS; classification/retention/sharing policy and template/engine versions are preserved. |
| RLS/audit | Cross-scope access is blocked by application and database backstops; every state change is attributable. |
| UX | All production routes pass keyboard, screen-reader semantics and agreed desktop/tablet/mobile visual tests. |
| Human quality | Blind SME gate passes separately for Knowledge Chat, Transaction Analysis and each Accounting Work case. |

## 13. Definition of product completion

The product is complete for this scope only when:

1. FigmaMake is the sole shipped UI.
2. Users can create a conversation or accounting case, upload and validate their evidence, run a
   bounded analysis, review findings and export a human-readable report.
3. Knowledge Chat correctly handles the ten-transaction anchor and cites governed BRAVO guidance.
4. Bank, Voucher and Period Close cases run on file-backed evidence rather than synthetic-only
   fixtures.
5. Knowledge/rules, Artifact Workspace, administration, retention and audit are usable in
   FigmaMake; shipped native Office formats pass semantic-integrity and fidelity gates.
6. No live BRAVO integration or duplicate accounting execution surface is reachable.
7. Frozen evals, blind SME review, RLS/security, offline and responsive/a11y gates pass.
8. Legacy frontend and retired feature code are archived/removed only after rollback and retention
   requirements are satisfied.

## 14. First implementation slice

The first slice should be limited to:

1. commit ADR-0035 and this consolidated plan, then record a clean implementation baseline and
   Alembic source head without reading secret stores;
2. generate the machine-readable feature inventory and obtain the retention disposition for
   historical draft/journal records;
3. change Docker/FastAPI/CI to build and serve `FigmaMake_UI`;
4. reduce FigmaMake production navigation to the section 3 allowlist;
5. unregister invoice-draft, journal-draft/export and connector routes behind a reversible feature
   flag, with negative contract tests; and
6. freeze only the minimum Import Pack schema families required by section 5 and the accepted P0
   fixtures.

Do not delete database records or start P2 accounting modules in this slice.

The second slice begins only after WP20-00/01/02 exits: implement the minimal file/evidence spine,
complete the independent SME gate for Plan 19's ten-transaction fixture, then build Conversation V2
contracts. Do not start an Office engine spike until the first verified semantic result and the
format-specific benchmark manifest exist.

## 15. Dev-handoff evidence and open gates

Observed during consolidation on 2026-08-19:

- repository commit: `9ae8192cbed60d76639cc93ed6511eada72a0f91`;
- worktree: **not clean** because Plan 20 was an untracked owner-provided file during review; this
  planning edit does not claim a clean implementation baseline;
- migration source/evidence identifies `0020_case_v2_audit` as the single head, but the current
  default Python invocation could not execute Alembic because the local `alembic/` package shadows
  the CLI module; WP20-00 must record the intended environment and a real probe when required;
- WP19-00 has a reproducible synthetic runtime image and a frozen 30-pair A/B artifact bound to
  model revision `gpt-4o-2024-11-20`; this closes baseline capture only, not a quality gate;
- WP19-01 records owner acceptance of the synthetic ten-transaction fixture and ADR-0034;
  independent accounting/BRAVO SME review remains open;
- current source still builds `frontend-react`, registers legacy connector/draft/invoice/graph
  routers and exposes journal draft/export tools. The standalone boundary is therefore a target
  decision until WP20-01/02 tests pass.

No prompt, routing, retrieval, synthesis, accounting engine or product runtime change is authorized
by claiming that the plan is ready. `READY FOR DEV HANDOFF` means the boundary, dependency order,
contracts and first slice are explicit enough for implementation to start at WP20-00 after the
decision set is committed.

## 16. Frontier and engine evidence used

These sources are architecture signals, not claims that BRAVO has matching quality or controls:

- [Microsoft Word/Excel/PowerPoint Agents](https://learn.microsoft.com/en-us/microsoft-365/copilot/wordexcelppt-agents): admin enablement, permission-scoped organizational context, enterprise data protection and tenant-owned generated files.
- [Microsoft Edit with Copilot in Excel](https://support.microsoft.com/en-us/office/agent-mode-in-excel-a2fd6fe4-97ac-416b-b89a-22f4d1357c7a): multi-step in-place editing with native tables, charts, PivotTables and formulas while the user controls changes.
- [Microsoft 365 Copilot data protection and audit](https://learn.microsoft.com/en-us/microsoft-365/copilot/microsoft-365-copilot-architecture-data-protection-auditing): access controls, sensitivity labels, retention and audit inheritance.
- [Google Slides presentation generation](https://support.google.com/docs/answer/17111393): source selection, editable plan, user approval, style reference and native editable output.
- [Canva Brand Templates](https://www.canva.com/business/features/team-templates/): centrally managed templates and locked brand elements.
- [Box AI configuration](https://support.box.com/hc/en-us/articles/22166647877011-Configuring-Box-AI): enterprise/user/group capability controls over AI document functions.
- [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI): agent-oriented create/edit/render candidate; repository claims and release cadence require independent fidelity validation.
- [Open XML SDK](https://github.com/dotnet/Open-XML-SDK): official low-level OOXML manipulation foundation and structural candidate, explicitly not a high-level productivity abstraction.
- [ONLYOFFICE Document Builder](https://github.com/ONLYOFFICE/DocumentBuilder): optional automation/editor candidate subject to AGPL/commercial licensing and watermark constraints in the free builder.
