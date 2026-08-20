import type { AccountingCaseView } from "../api/accountingCases";

/**
 * Test-only fixture source. It deliberately refuses non-fixture identifiers so QA data cannot
 * accidentally stand in for a server-backed accounting case on the production route.
 */
export type FixtureAccountingCaseSource = {
  get(caseId: string): Promise<AccountingCaseView>;
};

export function createFixtureAccountingCaseSource(cases: AccountingCaseView[]): FixtureAccountingCaseSource {
  const byId = new Map(cases.map(caseView => [caseView.case_id, caseView]));
  return {
    async get(caseId: string): Promise<AccountingCaseView> {
      if (!caseId.startsWith("fixture:")) {
        throw new Error(`Fixture source rejected non-fixture accounting case ID: ${caseId}`);
      }
      const caseView = byId.get(caseId);
      if (!caseView) throw new Error(`Fixture accounting case was not found: ${caseId}`);
      return caseView;
    },
  };
}
