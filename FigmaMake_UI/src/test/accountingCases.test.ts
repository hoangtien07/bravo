import { describe, expect, it, vi } from "vitest";

import { ApiError, createHttpClient } from "../api/http";
import { createAccountingCaseApi, decodeAccountingCase } from "../api/accountingCases";
import { canonicalReviewDecisionJson, hashReviewDecision, type UnsignedReviewDecision } from "../api/reviewDecisionHash";
import { createFixtureAccountingCaseSource } from "../accounting-work/data/source";

const scope = {
  tenant_id: "tenant-demo", legal_entity_id: "legal-entity-demo", ledger_id: "ledger-vnd", period: "2026-06",
  cutoff: "2026-06-30", currency: "VND", environment: "synthetic", bravo_version: "B10R1", config_version: "wp01/v1",
  bank_account_ref: "1121",
};

const caseView = {
  case_id: "case_12345678", case_type: "bank_reconciliation", scope, state: "NEEDS_REVIEW", revision: 4,
  evidence: [], results: [], findings: [], review_decisions: [], draft_payload_hash: "a".repeat(64),
  evidence_hash: "b".repeat(64), result_hash: "c".repeat(64), approval: null,
  trace: { contract_version: "wp04/v1", raw_evidence_retained: false },
};

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

describe("AccountingCase API boundary", () => {
  it("decodes the durable case read model and rejects an unknown state", () => {
    expect(decodeAccountingCase(caseView)).toMatchObject({ case_id: "case_12345678", state: "NEEDS_REVIEW" });
    expect(() => decodeAccountingCase({ ...caseView, state: "RECONCILED" })).toThrow(ApiError);
  });

  it("sends bearer auth and the exact create payload", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(response(caseView));
    const api = createAccountingCaseApi({ fetchImpl, getToken: () => "test-token" });
    await api.create({ scope, case_type: "bank_reconciliation", idempotency_key: "create-001" });

    const [path, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/v2/accounting-cases");
    expect(init.method).toBe("POST");
    expect(new Headers(init.headers).get("authorization")).toBe("Bearer test-token");
    expect(JSON.parse(String(init.body))).toMatchObject({ case_type: "bank_reconciliation", idempotency_key: "create-001" });
  });

  it("rejects a fixture identifier before the live request is built", async () => {
    const fetchImpl = vi.fn();
    const api = createAccountingCaseApi({ fetchImpl });
    await expect(api.get("fixture:case:0001")).rejects.toThrow(/Fixture identifier/);
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("normalizes an API revision conflict", async () => {
    const http = createHttpClient({ fetchImpl: vi.fn().mockResolvedValue(response({ detail: "stale revision" }, 409)) });
    await expect(http.requestJson("/api/v2/accounting-cases/case_12345678", { method: "GET" }, value => value)).rejects.toMatchObject({
      kind: "conflict", status: 409, message: "stale revision",
    });
  });

  it("keeps fixture sources local and rejects a live ID", async () => {
    const fixture = { ...decodeAccountingCase(caseView), case_id: "fixture:case:0001" };
    const source = createFixtureAccountingCaseSource([fixture]);
    await expect(source.get("fixture:case:0001")).resolves.toEqual(fixture);
    await expect(source.get("case_12345678")).rejects.toThrow(/Fixture source rejected/);
  });
});

describe("reviewer decision hash", () => {
  const decision: UnsignedReviewDecision = {
    finding_id: "finding-001", disposition: "resolved", reviewer_id: "reviewer-42",
    reason_code: "EVIDENCE_CONFIRMED", note: "Evidence reviewed.",
    evidence_snapshot_ids: ["snapshot-1", "snapshot-2"],
  };

  it("uses the canonical JSON representation shared with the backend", () => {
    expect(canonicalReviewDecisionJson(decision)).toBe('{"disposition":"resolved","evidence_snapshot_ids":["snapshot-1","snapshot-2"],"finding_id":"finding-001","note":"Evidence reviewed.","reason_code":"EVIDENCE_CONFIRMED","reviewer_id":"reviewer-42"}');
  });

  it("matches the frozen SHA-256 vector", async () => {
    await expect(hashReviewDecision(decision)).resolves.toBe("9af456f98d59e4e73a22d9e4f994bf0a13510f223ddf00f7fddce009446679e6");
  });
});

