import { ApiError, createHttpClient, type HttpClient, type HttpClientOptions } from "./http";

export const ACCOUNTING_CASE_API_ROOT = "/api/v2/accounting-cases";

export type CaseType = "bank_reconciliation" | "voucher_evidence_review" | "period_close_readiness";
export type CaseState = "NEW" | "SCOPE_LOCKED" | "EVIDENCE_PENDING" | "EVIDENCE_READY" | "CHECKED"
  | "NEEDS_REVIEW" | "REVIEWED" | "EXPORTED" | "CLOSED" | "ABSTAINED" | "FAILED" | "CANCELLED" | "SUPERSEDED";
export type ReviewDisposition = "investigate" | "resolved" | "accepted_exception" | "escalate";
export type JsonRecord = Record<string, unknown>;

export type ScopeKey = {
  tenant_id: string;
  legal_entity_id: string;
  ledger_id: string;
  period: string;
  cutoff: string;
  currency: string;
  environment: string;
  bravo_version: string;
  config_version: string;
  bank_account_ref?: string | null;
};

export type EvidenceSnapshotView = {
  snapshot_id: string;
  source_type: string;
  source_version: string;
  cutoff: string;
  captured_at: string;
  content_hash: string;
  supersedes: string | null;
  complete: boolean;
  scope: ScopeKey;
};

export type DeterministicCheckView = {
  check_id: string;
  rule_version: string;
  inputs: JsonRecord;
  result: JsonRecord;
  reason_code: string;
  lineage_snapshot_ids: string[];
};

export type FindingView = {
  finding_id: string;
  finding_type: string;
  severity: string;
  status: string;
  evidence_snapshot_ids: string[];
  check_result_ids: string[];
  reviewer_disposition: string | null;
};

export type ReviewDecision = {
  finding_id: string;
  disposition: ReviewDisposition;
  reviewer_id: string;
  reason_code: string;
  note: string | null;
  evidence_snapshot_ids: string[];
  decision_hash: string;
};

export type ApprovalView = JsonRecord & {
  maker_id: string;
  checker_id: string;
  payload_hash: string;
  policy_version: string;
  approved_at: string;
  evidence_hash?: string | null;
  result_hash?: string | null;
  review_hash?: string | null;
};

export type AccountingCaseView = {
  case_id: string;
  case_type: CaseType;
  scope: ScopeKey;
  state: CaseState;
  revision: number;
  evidence: EvidenceSnapshotView[];
  results: DeterministicCheckView[];
  findings: FindingView[];
  review_decisions: ReviewDecision[];
  draft_payload_hash: string | null;
  evidence_hash: string;
  result_hash: string | null;
  approval: ApprovalView | null;
  trace: JsonRecord;
};

export type ExportedCase = { case: AccountingCaseView; artifact: JsonRecord };

export type AccountingConversationReply = {
  kind: "explanation" | "clarification" | "abstention";
  text: string;
  finding_ids: string[];
  evidence_snapshot_ids: string[];
  rule_ids: string[];
  mutates_case: false;
};

export type CreateCaseInput = { scope: ScopeKey; case_type: CaseType; idempotency_key: string };
export type MutationInput = { expected_revision: number; idempotency_key: string };
export type EvidenceInput = MutationInput & { replacement_source_type?: string };
export type ReviewInput = MutationInput & {
  decisions: ReviewDecision[];
  payload_hash: string;
  evidence_hash: string;
  result_hash: string;
};
export type ExportInput = MutationInput & { payload_hash: string; evidence_hash: string; review_hash: string };

export type AccountingCaseApi = {
  list(signal?: AbortSignal): Promise<AccountingCaseView[]>;
  create(input: CreateCaseInput, signal?: AbortSignal): Promise<AccountingCaseView>;
  get(caseId: string, signal?: AbortSignal): Promise<AccountingCaseView>;
  attachEvidence(caseId: string, input: EvidenceInput, signal?: AbortSignal): Promise<AccountingCaseView>;
  runChecks(caseId: string, input: MutationInput, signal?: AbortSignal): Promise<AccountingCaseView>;
  review(caseId: string, input: ReviewInput, signal?: AbortSignal): Promise<AccountingCaseView>;
  export(caseId: string, input: ExportInput, signal?: AbortSignal): Promise<ExportedCase>;
  explainBankFinding(caseId: string, question: string, signal?: AbortSignal): Promise<AccountingConversationReply>;
};

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function contractError(path: string): never {
  throw new ApiError("server", 200, `Phản hồi API không đúng contract tại ${path}.`);
}

function stringAt(value: JsonRecord, key: string, path: string): string {
  const item = value[key];
  return typeof item === "string" ? item : contractError(`${path}.${key}`);
}

function nullableStringAt(value: JsonRecord, key: string, path: string): string | null {
  const item = value[key];
  return item === null || typeof item === "string" ? item : contractError(`${path}.${key}`);
}

function numberAt(value: JsonRecord, key: string, path: string): number {
  const item = value[key];
  return typeof item === "number" && Number.isFinite(item) ? item : contractError(`${path}.${key}`);
}

function booleanAt(value: JsonRecord, key: string, path: string): boolean {
  const item = value[key];
  return typeof item === "boolean" ? item : contractError(`${path}.${key}`);
}

function recordAt(value: JsonRecord, key: string, path: string): JsonRecord {
  const item = value[key];
  return isRecord(item) ? item : contractError(`${path}.${key}`);
}

function nullableRecordAt(value: JsonRecord, key: string, path: string): JsonRecord | null {
  const item = value[key];
  return item === null || isRecord(item) ? item : contractError(`${path}.${key}`);
}

function arrayAt(value: JsonRecord, key: string, path: string): unknown[] {
  const item = value[key];
  return Array.isArray(item) ? item : contractError(`${path}.${key}`);
}

function stringArray(value: unknown, path: string): string[] {
  return Array.isArray(value) && value.every(item => typeof item === "string") ? [...value] : contractError(path);
}

function oneOf<T extends string>(value: string, allowed: readonly T[], path: string): T {
  return (allowed as readonly string[]).includes(value) ? value as T : contractError(path);
}

const CASE_TYPES = ["bank_reconciliation", "voucher_evidence_review", "period_close_readiness"] as const;
const CASE_STATES = ["NEW", "SCOPE_LOCKED", "EVIDENCE_PENDING", "EVIDENCE_READY", "CHECKED", "NEEDS_REVIEW", "REVIEWED", "EXPORTED", "CLOSED", "ABSTAINED", "FAILED", "CANCELLED", "SUPERSEDED"] as const;
const REVIEW_DISPOSITIONS = ["investigate", "resolved", "accepted_exception", "escalate"] as const;

export function decodeScopeKey(value: unknown, path = "scope"): ScopeKey {
  if (!isRecord(value)) return contractError(path);
  const bankAccountRef = value.bank_account_ref;
  if (bankAccountRef !== undefined && bankAccountRef !== null && typeof bankAccountRef !== "string") contractError(`${path}.bank_account_ref`);
  return {
    tenant_id: stringAt(value, "tenant_id", path), legal_entity_id: stringAt(value, "legal_entity_id", path),
    ledger_id: stringAt(value, "ledger_id", path), period: stringAt(value, "period", path),
    cutoff: stringAt(value, "cutoff", path), currency: stringAt(value, "currency", path),
    environment: stringAt(value, "environment", path), bravo_version: stringAt(value, "bravo_version", path),
    config_version: stringAt(value, "config_version", path), bank_account_ref: bankAccountRef ?? null,
  };
}

function decodeEvidence(value: unknown, path: string): EvidenceSnapshotView {
  if (!isRecord(value)) return contractError(path);
  return {
    snapshot_id: stringAt(value, "snapshot_id", path), source_type: stringAt(value, "source_type", path),
    source_version: stringAt(value, "source_version", path), cutoff: stringAt(value, "cutoff", path),
    captured_at: stringAt(value, "captured_at", path), content_hash: stringAt(value, "content_hash", path),
    supersedes: nullableStringAt(value, "supersedes", path), complete: booleanAt(value, "complete", path),
    scope: decodeScopeKey(value.scope, `${path}.scope`),
  };
}

function decodeResult(value: unknown, path: string): DeterministicCheckView {
  if (!isRecord(value)) return contractError(path);
  return {
    check_id: stringAt(value, "check_id", path), rule_version: stringAt(value, "rule_version", path),
    inputs: recordAt(value, "inputs", path), result: recordAt(value, "result", path),
    reason_code: stringAt(value, "reason_code", path), lineage_snapshot_ids: stringArray(value.lineage_snapshot_ids, `${path}.lineage_snapshot_ids`),
  };
}

function decodeFinding(value: unknown, path: string): FindingView {
  if (!isRecord(value)) return contractError(path);
  return {
    finding_id: stringAt(value, "finding_id", path), finding_type: stringAt(value, "finding_type", path),
    severity: stringAt(value, "severity", path), status: stringAt(value, "status", path),
    evidence_snapshot_ids: stringArray(value.evidence_snapshot_ids, `${path}.evidence_snapshot_ids`),
    check_result_ids: stringArray(value.check_result_ids, `${path}.check_result_ids`),
    reviewer_disposition: nullableStringAt(value, "reviewer_disposition", path),
  };
}

function decodeReviewDecision(value: unknown, path: string): ReviewDecision {
  if (!isRecord(value)) return contractError(path);
  return {
    finding_id: stringAt(value, "finding_id", path),
    disposition: oneOf(stringAt(value, "disposition", path), REVIEW_DISPOSITIONS, `${path}.disposition`),
    reviewer_id: stringAt(value, "reviewer_id", path), reason_code: stringAt(value, "reason_code", path),
    note: nullableStringAt(value, "note", path), evidence_snapshot_ids: stringArray(value.evidence_snapshot_ids, `${path}.evidence_snapshot_ids`),
    decision_hash: stringAt(value, "decision_hash", path),
  };
}

export function decodeAccountingCase(value: unknown, path = "case"): AccountingCaseView {
  if (!isRecord(value)) return contractError(path);
  const approval = nullableRecordAt(value, "approval", path);
  return {
    case_id: stringAt(value, "case_id", path), case_type: oneOf(stringAt(value, "case_type", path), CASE_TYPES, `${path}.case_type`),
    scope: decodeScopeKey(value.scope, `${path}.scope`), state: oneOf(stringAt(value, "state", path), CASE_STATES, `${path}.state`),
    revision: numberAt(value, "revision", path),
    evidence: arrayAt(value, "evidence", path).map((item, index) => decodeEvidence(item, `${path}.evidence[${index}]`)),
    results: arrayAt(value, "results", path).map((item, index) => decodeResult(item, `${path}.results[${index}]`)),
    findings: arrayAt(value, "findings", path).map((item, index) => decodeFinding(item, `${path}.findings[${index}]`)),
    review_decisions: arrayAt(value, "review_decisions", path).map((item, index) => decodeReviewDecision(item, `${path}.review_decisions[${index}]`)),
    draft_payload_hash: nullableStringAt(value, "draft_payload_hash", path), evidence_hash: stringAt(value, "evidence_hash", path),
    result_hash: nullableStringAt(value, "result_hash", path), approval: approval as ApprovalView | null,
    trace: recordAt(value, "trace", path),
  };
}

function decodeCaseList(value: unknown): AccountingCaseView[] {
  return Array.isArray(value) ? value.map((item, index) => decodeAccountingCase(item, `cases[${index}]`)) : contractError("cases");
}

function decodeExportedCase(value: unknown): ExportedCase {
  if (!isRecord(value)) return contractError("export");
  return { case: decodeAccountingCase(value.case, "export.case"), artifact: recordAt(value, "artifact", "export") };
}

function decodeConversation(value: unknown): AccountingConversationReply {
  if (!isRecord(value)) return contractError("conversation");
  const mutatesCase = booleanAt(value, "mutates_case", "conversation");
  if (mutatesCase) return contractError("conversation.mutates_case");
  return {
    kind: oneOf(stringAt(value, "kind", "conversation"), ["explanation", "clarification", "abstention"] as const, "conversation.kind"),
    text: stringAt(value, "text", "conversation"), finding_ids: stringArray(value.finding_ids, "conversation.finding_ids"),
    evidence_snapshot_ids: stringArray(value.evidence_snapshot_ids, "conversation.evidence_snapshot_ids"),
    rule_ids: stringArray(value.rule_ids, "conversation.rule_ids"), mutates_case: false,
  };
}

function assertNoFixtureIdentifiers(value: unknown, path = "request"): void {
  if (typeof value === "string") {
    if (value.startsWith("fixture:")) throw new Error(`Fixture identifier cannot be sent to live API (${path}).`);
    return;
  }
  if (Array.isArray(value)) value.forEach((item, index) => assertNoFixtureIdentifiers(item, `${path}[${index}]`));
  else if (isRecord(value)) Object.entries(value).forEach(([key, item]) => assertNoFixtureIdentifiers(item, `${path}.${key}`));
}

function jsonBody(value: JsonRecord): string {
  assertNoFixtureIdentifiers(value);
  return JSON.stringify(value);
}

function liveCasePath(caseId: string): string {
  assertNoFixtureIdentifiers(caseId, "case_id");
  return `${ACCOUNTING_CASE_API_ROOT}/${encodeURIComponent(caseId)}`;
}

function defaultHttp(options?: HttpClientOptions): HttpClient {
  return createHttpClient(options);
}

export function createAccountingCaseApi(options: HttpClientOptions & { http?: HttpClient } = {}): AccountingCaseApi {
  const http = options.http ?? defaultHttp(options);
  const request = async <T>(path: string, method: string, body: JsonRecord | undefined, decode: (value: unknown) => T, signal?: AbortSignal): Promise<T> => {
    const serialized = body === undefined ? undefined : jsonBody(body);
    return http.requestJson(path, { method, signal, body: serialized }, decode);
  };

  return {
    list: signal => request(ACCOUNTING_CASE_API_ROOT, "GET", undefined, decodeCaseList, signal),
    create: (input, signal) => request(ACCOUNTING_CASE_API_ROOT, "POST", input, decodeAccountingCase, signal),
    get: async (caseId, signal) => request(liveCasePath(caseId), "GET", undefined, decodeAccountingCase, signal),
    attachEvidence: async (caseId, input, signal) => request(`${liveCasePath(caseId)}/evidence`, "POST", input, decodeAccountingCase, signal),
    runChecks: async (caseId, input, signal) => request(`${liveCasePath(caseId)}/run-checks`, "POST", input, decodeAccountingCase, signal),
    review: async (caseId, input, signal) => request(`${liveCasePath(caseId)}/review`, "POST", input, decodeAccountingCase, signal),
    export: async (caseId, input, signal) => request(`${liveCasePath(caseId)}/export`, "POST", input, decodeExportedCase, signal),
    explainBankFinding: async (caseId, question, signal) => request(`${liveCasePath(caseId)}/conversation`, "POST", { question }, decodeConversation, signal),
  };
}

export function createIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID();
  return `case-ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
