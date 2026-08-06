import { ApiError, type FetchLike } from "./http";

export type AuthConfig = { oidcEnabled: boolean };

export type AuthIdentity = {
  id: string;
  fullName: string;
  departmentIds: string[];
  isAdmin: boolean;
  permissions: string[];
};

function asRecord(value: unknown, path: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new ApiError("server", 200, `Phản hồi xác thực không đúng contract tại ${path}.`);
  return value as Record<string, unknown>;
}

function requiredString(value: Record<string, unknown>, key: string, path: string): string {
  if (typeof value[key] !== "string") throw new ApiError("server", 200, `Phản hồi xác thực không đúng contract tại ${path}.${key}.`);
  return value[key];
}

async function request(fetchImpl: FetchLike, path: string, init?: RequestInit): Promise<unknown> {
  let response: Response;
  try {
    response = await fetchImpl(path, init);
  } catch (error) {
    throw new ApiError("network", null, error instanceof Error ? error.message : "Không thể kết nối dịch vụ xác thực.", error);
  }
  const json = response.headers.get("content-type")?.includes("application/json") ? await response.json().catch(() => undefined) : undefined;
  if (!response.ok) {
    const detail = typeof json === "object" && json !== null && "detail" in json ? (json as { detail?: unknown }).detail : undefined;
    const message = typeof detail === "string" && detail.trim() ? detail : `Yêu cầu xác thực không thành công (${response.status}).`;
    const kind = response.status === 401 ? "unauthorized" : response.status === 403 ? "denied" : response.status === 404 ? "unavailable" : response.status === 422 ? "invalid" : "server";
    throw new ApiError(kind, response.status, message, json);
  }
  return json;
}

export function createAuthApi(fetchImpl: FetchLike = globalThis.fetch.bind(globalThis)) {
  return {
    async config(): Promise<AuthConfig> {
      const body = asRecord(await request(fetchImpl, "/api/auth/config", { headers: { accept: "application/json" } }), "auth.config");
      if (typeof body.oidc_enabled !== "boolean") throw new ApiError("server", 200, "Phản hồi xác thực không đúng contract tại auth.config.oidc_enabled.");
      return { oidcEnabled: body.oidc_enabled };
    },
    async passwordLogin(email: string, password: string): Promise<string> {
      const body = asRecord(await request(fetchImpl, "/api/auth/login", {
        method: "POST",
        headers: { accept: "application/json", "content-type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password }).toString(),
      }), "auth.login");
      return requiredString(body, "access_token", "auth.login");
    },
    async me(token: string): Promise<AuthIdentity> {
      const body = asRecord(await request(fetchImpl, "/api/me", { headers: { accept: "application/json", authorization: `Bearer ${token}` } }), "auth.me");
      const permissions = body.permissions;
      const departments = body.department_ids;
      if (!Array.isArray(permissions) || !permissions.every(item => typeof item === "string")) throw new ApiError("server", 200, "Phản hồi xác thực không đúng contract tại auth.me.permissions.");
      if (!Array.isArray(departments) || !departments.every(item => typeof item === "string")) throw new ApiError("server", 200, "Phản hồi xác thực không đúng contract tại auth.me.department_ids.");
      if (typeof body.is_admin !== "boolean") throw new ApiError("server", 200, "Phản hồi xác thực không đúng contract tại auth.me.is_admin.");
      return { id: requiredString(body, "id", "auth.me"), fullName: requiredString(body, "full_name", "auth.me"), departmentIds: departments, isAdmin: body.is_admin, permissions };
    },
  };
}
