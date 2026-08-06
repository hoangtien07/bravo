import { ApiError, candidateToken } from "./http";

export type ChatAttachment = {
  id: string;
  filename: string;
  mimeType: string;
  sizeBytes: number;
  kind: string;
  status: string;
  error: string | null;
};

export type WorkspaceSource = {
  id: string;
  filename: string;
  status: string;
  visibility: string;
};

function object(value: unknown, path: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new ApiError("server", 200, `Evidence response is invalid at ${path}.`);
  return value as Record<string, unknown>;
}
function required(row: Record<string, unknown>, key: string, path: string): string {
  if (typeof row[key] !== "string") throw new ApiError("server", 200, `Evidence response is invalid at ${path}.${key}.`);
  return row[key] as string;
}
function number(row: Record<string, unknown>, key: string, path: string): number {
  if (typeof row[key] !== "number") throw new ApiError("server", 200, `Evidence response is invalid at ${path}.${key}.`);
  return row[key] as number;
}
function failure(response: Response, detail: unknown): ApiError {
  const kind = response.status === 401 ? "unauthorized" : response.status === 403 ? "denied" : response.status === 404 ? "unavailable" : response.status === 409 ? "conflict" : response.status === 422 ? "invalid" : "server";
  const message = typeof detail === "object" && detail !== null && "detail" in detail && typeof (detail as { detail?: unknown }).detail === "string" ? (detail as { detail: string }).detail : `Evidence request failed (${response.status}).`;
  return new ApiError(kind, response.status, message, detail);
}
async function request(path: string, init: RequestInit): Promise<unknown> {
  const token = candidateToken();
  if (!token) throw new ApiError("unauthorized", 401, "Your sign-in session has expired.");
  const headers = new Headers(init.headers);
  headers.set("accept", "application/json");
  headers.set("authorization", `Bearer ${token}`);
  let response: Response;
  try { response = await fetch(path, { ...init, headers }); } catch (cause) { throw new ApiError("network", null, "Cannot connect to the evidence service.", cause); }
  const body = await response.json().catch(() => undefined);
  if (!response.ok) throw failure(response, body);
  return body;
}
function decodeAttachment(value: unknown): ChatAttachment {
  const row = object(value, "attachment");
  return { id: required(row, "id", "attachment"), filename: required(row, "filename", "attachment"), mimeType: required(row, "mime_type", "attachment"), sizeBytes: number(row, "size_bytes", "attachment"), kind: required(row, "kind", "attachment"), status: required(row, "status", "attachment"), error: row.error === null || row.error === undefined ? null : required(row, "error", "attachment") };
}
function decodeSource(value: unknown, path: string): WorkspaceSource {
  const row = object(value, path);
  return { id: required(row, "id", path), filename: required(row, "filename", path), status: required(row, "status", path), visibility: required(row, "visibility", path) };
}

export const evidenceApi = {
  async uploadAttachment(file: File): Promise<ChatAttachment> {
    const form = new FormData(); form.append("file", file);
    return decodeAttachment(await request("/api/attachments", { method: "POST", body: form }));
  },
  async getAttachment(id: string): Promise<ChatAttachment> { return decodeAttachment(await request(`/api/attachments/${encodeURIComponent(id)}`, {})); },
  async removeAttachment(id: string): Promise<void> { await request(`/api/attachments/${encodeURIComponent(id)}`, { method: "DELETE" }); },
  async listSources(): Promise<WorkspaceSource[]> {
    const body = await request("/api/sources", {});
    if (!Array.isArray(body)) throw new ApiError("server", 200, "Evidence source list is invalid.");
    return body.map((value, index) => decodeSource(value, `sources[${index}]`));
  },
};
