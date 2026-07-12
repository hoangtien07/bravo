// Workspace + chat-attachment API (v2). Multipart uploads use fetch directly (api<T> is JSON).
import { api, authHeaders } from "./client";
import type { Attachment, SourceItem } from "./types";

async function multipart<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(path, { method: "POST", headers: authHeaders(), body: form });
  if (!res.ok) {
    let detail = `Lỗi ${res.status}`;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

// --- chat attachments --- //
export function uploadAttachment(file: File): Promise<Attachment> {
  const form = new FormData();
  form.append("file", file);
  return multipart<Attachment>("/api/attachments", form);
}

export function getAttachment(id: string): Promise<Attachment> {
  return api<Attachment>(`/api/attachments/${id}`);
}

export function deleteAttachment(id: string): Promise<void> {
  return api<void>(`/api/attachments/${id}`, { method: "DELETE" });
}

// --- workspace documents --- //
export function listSources(scope: "mine" | "department" | "global" | "all" = "all"): Promise<SourceItem[]> {
  return api<SourceItem[]>(`/api/sources?scope=${scope}`);
}

export function uploadSource(
  file: File,
  visibility: "personal" | "department" | "global",
  opts: { knowledge_type?: string; department_ids?: string } = {}
): Promise<SourceItem> {
  const form = new FormData();
  form.append("file", file);
  form.append("visibility", visibility);
  if (opts.knowledge_type) form.append("knowledge_type", opts.knowledge_type);
  if (opts.department_ids) form.append("department_ids", opts.department_ids);
  return multipart<SourceItem>("/api/sources", form);
}

export function deleteSource(id: string): Promise<void> {
  return api<void>(`/api/sources/${id}`, { method: "DELETE" });
}
