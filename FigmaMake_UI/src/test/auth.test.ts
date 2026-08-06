import { describe, expect, it, vi } from "vitest";
import { createAuthApi } from "../api/auth";

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

describe("candidate auth API boundary", () => {
  it("uses form login, reads OIDC capability and validates /api/me", async () => {
    const fetchImpl = vi.fn()
      .mockResolvedValueOnce(response({ oidc_enabled: true }))
      .mockResolvedValueOnce(response({ access_token: "candidate-token", token_type: "bearer" }))
      .mockResolvedValueOnce(response({ id: "user-1", full_name: "Reviewer", department_ids: ["dept-1"], is_admin: false, permissions: ["accounting_case:review:*"] }));
    const api = createAuthApi(fetchImpl);
    await expect(api.config()).resolves.toEqual({ oidcEnabled: true });
    await expect(api.passwordLogin("reviewer@bravo.vn", "not-a-secret")).resolves.toBe("candidate-token");
    await expect(api.me("candidate-token")).resolves.toMatchObject({ id: "user-1", permissions: ["accounting_case:review:*"] });

    const [, loginRequest] = fetchImpl.mock.calls[1] as [string, RequestInit];
    expect(loginRequest.headers).toMatchObject({ "content-type": "application/x-www-form-urlencoded" });
    expect(loginRequest.body).toBe("username=reviewer%40bravo.vn&password=not-a-secret");
  });

  it("does not accept a malformed identity response", async () => {
    const api = createAuthApi(vi.fn().mockResolvedValue(response({ id: "user-1", full_name: "X", department_ids: [], is_admin: false, permissions: "bad" })));
    await expect(api.me("candidate-token")).rejects.toThrow(/permissions/);
  });
});
