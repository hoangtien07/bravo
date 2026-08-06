import type { ReviewDecision, ReviewDisposition } from "./accountingCases";

export type UnsignedReviewDecision = Omit<ReviewDecision, "decision_hash"> & { disposition: ReviewDisposition };

/**
 * Canonical wire representation matching SyntheticBankCaseService.review_decision_hash:
 * UTF-8 SHA-256 of JSON with sorted keys, compact separators and literal Unicode characters.
 */
export function canonicalReviewDecisionJson(decision: UnsignedReviewDecision): string {
  return JSON.stringify({
    disposition: decision.disposition,
    evidence_snapshot_ids: decision.evidence_snapshot_ids,
    finding_id: decision.finding_id,
    note: decision.note,
    reason_code: decision.reason_code,
    reviewer_id: decision.reviewer_id,
  });
}

export async function hashReviewDecision(decision: UnsignedReviewDecision): Promise<string> {
  if (!globalThis.crypto?.subtle) throw new Error("Trình duyệt không hỗ trợ Web Crypto cho reviewer decision hash.");
  const payload = new TextEncoder().encode(canonicalReviewDecisionJson(decision));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", payload);
  return Array.from(new Uint8Array(digest), item => item.toString(16).padStart(2, "0")).join("");
}

