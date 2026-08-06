import { ApiError, candidateToken } from "./http";

export type ConversationSummary = { id: string; title: string; lastMessageAt: string | null; createdAt: string };
export type ConversationMessage = { id: string; role: "user" | "assistant"; content: string; createdAt: string; feedback: "like" | "dislike" | null };
export type Conversation = { id: string; title: string; messages: ConversationMessage[] };
export type SharedConversation = { title: string; messages: ConversationMessage[] };
export type StreamEvent = { type: string; [key: string]: unknown };
export type ChatTurnOptions = { attachmentIds?: string[]; sourceIds?: string[] };
const KNOWN_STREAM_EVENT_TYPES = new Set(["id", "plan", "plan_update", "source", "attachments", "status", "step", "tool_call", "tool_result", "artifact", "draft", "answer", "done", "error", "ping"]);

function record(value: unknown, path: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new ApiError("server", 200, `Phản hồi hội thoại không đúng contract tại ${path}.`);
  return value as Record<string, unknown>;
}
function string(value: Record<string, unknown>, key: string, path: string): string {
  if (typeof value[key] !== "string") throw new ApiError("server", 200, `Phản hồi hội thoại không đúng contract tại ${path}.${key}.`);
  return value[key] as string;
}
function nullableString(value: Record<string, unknown>, key: string, path: string): string | null {
  if (value[key] === null) return null;
  return string(value, key, path);
}
function decodeMessage(value: unknown, path: string): ConversationMessage {
  const row = record(value, path); const role = string(row, "role", path);
  if (role !== "user" && role !== "assistant") throw new ApiError("server", 200, `Vai trò tin nhắn không được hỗ trợ tại ${path}.role.`);
  const feedback = row.feedback;
  if (feedback !== null && feedback !== "like" && feedback !== "dislike") throw new ApiError("server", 200, `Phản hồi tin nhắn không đúng contract tại ${path}.feedback.`);
  return { id: string(row, "id", path), role, content: string(row, "content", path), createdAt: string(row, "created_at", path), feedback };
}
function decodeConversation(value: unknown): Conversation {
  const row = record(value, "conversation");
  if (!Array.isArray(row.messages)) throw new ApiError("server", 200, "Phản hồi hội thoại không đúng contract tại conversation.messages.");
  return { id: string(row, "id", "conversation"), title: string(row, "title", "conversation"), messages: row.messages.map((item, index) => decodeMessage(item, `conversation.messages[${index}]`)) };
}
function failure(response: Response, detail: unknown): ApiError {
  const kind = response.status === 401 ? "unauthorized" : response.status === 403 ? "denied" : response.status === 404 ? "unavailable" : response.status === 409 ? "conflict" : response.status === 422 ? "invalid" : "server";
  const message = typeof detail === "object" && detail !== null && "detail" in detail && typeof (detail as { detail?: unknown }).detail === "string" ? (detail as { detail: string }).detail : `Yêu cầu hội thoại không thành công (${response.status}).`;
  return new ApiError(kind, response.status, message, detail);
}
function liveConversationId(id: string): string {
  if (!id || id.startsWith("fixture:")) throw new ApiError("invalid", 422, "Fixture conversation identifiers are not valid on a live route.");
  return encodeURIComponent(id);
}
async function jsonRequest(path: string, init: RequestInit = {}, publicRequest = false): Promise<unknown> {
  const headers = new Headers(init.headers); headers.set("accept", "application/json");
  if (!publicRequest) { const token = candidateToken(); if (!token) throw new ApiError("unauthorized", 401, "Phiên đăng nhập đã hết hạn."); headers.set("authorization", `Bearer ${token}`); }
  let response: Response;
  try { response = await fetch(path, { ...init, headers }); } catch (cause) { throw new ApiError("network", null, "Không thể kết nối dịch vụ hội thoại.", cause); }
  const body = await response.json().catch(() => undefined);
  if (!response.ok) throw failure(response, body);
  return body;
}

export function createConversationId(): string { return crypto.randomUUID(); }

export const conversationsApi = {
  async list(): Promise<ConversationSummary[]> {
    const body = await jsonRequest("/api/conversations");
    if (!Array.isArray(body)) throw new ApiError("server", 200, "Phản hồi danh sách hội thoại không đúng contract.");
    return body.map((value, index) => { const row = record(value, `conversations[${index}]`); return { id: string(row, "id", `conversations[${index}]`), title: string(row, "title", `conversations[${index}]`), lastMessageAt: nullableString(row, "last_message_at", `conversations[${index}]`), createdAt: string(row, "created_at", `conversations[${index}]`) }; });
  },
  async get(id: string): Promise<Conversation> { return decodeConversation(await jsonRequest(`/api/conversations/${liveConversationId(id)}`)); },
  async rename(id: string, title: string): Promise<Conversation> { return decodeConversation(await jsonRequest(`/api/conversations/${liveConversationId(id)}/rename`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ title }) })); },
  async remove(id: string): Promise<void> { await jsonRequest(`/api/conversations/${liveConversationId(id)}`, { method: "DELETE" }); },
  async truncate(id: string, fromMessageId: string, inclusive = true): Promise<number> { const row = record(await jsonRequest(`/api/conversations/${liveConversationId(id)}/truncate`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ from_message_id: fromMessageId, inclusive }) }), "truncate"); if (typeof row.deleted !== "number") throw new ApiError("server", 200, "Phản hồi cắt hội thoại không đúng contract."); return row.deleted; },
  async share(id: string): Promise<{ token: string; url: string }> { const row = record(await jsonRequest(`/api/conversations/${liveConversationId(id)}/share`, { method: "POST" }), "share"); return { token: string(row, "shared_token", "share"), url: string(row, "url", "share") }; },
  async unshare(id: string): Promise<void> { await jsonRequest(`/api/conversations/${liveConversationId(id)}/share`, { method: "DELETE" }); },
  async shared(token: string): Promise<SharedConversation> { const row = record(await jsonRequest(`/api/shared/${encodeURIComponent(token)}`, {}, true), "shared"); if (!Array.isArray(row.messages)) throw new ApiError("server", 200, "Phản hồi chia sẻ không đúng contract."); return { title: string(row, "title", "shared"), messages: row.messages.map((item, index) => decodeMessage(item, `shared.messages[${index}]`)) }; },
  async feedback(conversationId: string, messageId: string, value: "like" | "dislike" | null): Promise<void> { await jsonRequest(`/api/conversations/${liveConversationId(conversationId)}/messages/${encodeURIComponent(messageId)}/feedback`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ value }) }); },
  async stream(conversationId: string, question: string, onEvent: (event: StreamEvent) => void, signal: AbortSignal, options: ChatTurnOptions = {}): Promise<void> {
    const token = candidateToken(); if (!token) throw new ApiError("unauthorized", 401, "Phiên đăng nhập đã hết hạn.");
    let response: Response;
    const liveId = liveConversationId(conversationId);
    try { response = await fetch(`/api/chat/${liveId}/messages`, { method: "POST", headers: { accept: "text/event-stream", "content-type": "application/json", authorization: `Bearer ${token}` }, body: JSON.stringify({ question, mode: "auto", web_access: "off", consultant_mode: "auto", consultant_profile: "auto", attachment_ids: options.attachmentIds ?? [], source_ids: options.sourceIds ?? [] }), signal }); } catch (cause) { if (signal.aborted) return; throw new ApiError("network", null, "Không thể kết nối luồng trả lời.", cause); }
    if (!response.ok) throw failure(response, await response.json().catch(() => undefined));
    if (!response.body) throw new ApiError("server", response.status, "Máy chủ không trả về luồng SSE.");
    const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ""; let terminalDone = false; let terminalError = false;
    const flush = () => { const records = buffer.split(/\r?\n\r?\n/); buffer = records.pop() ?? ""; for (const recordText of records) { const data = recordText.split(/\r?\n/).filter(line => line.startsWith("data:")).map(line => line.slice(5).trimStart()).join("\n"); if (!data) continue; try { const event = JSON.parse(data); if (!event || typeof event !== "object" || typeof event.type !== "string") { onEvent({ type: "error", message: "Bản ghi SSE không đúng contract." }); continue; } if (!KNOWN_STREAM_EVENT_TYPES.has(event.type)) { onEvent({ type: "error", message: `SSE event không được hỗ trợ: ${event.type}.` }); terminalError = true; continue; } if (event.type === "done") terminalDone = true; if (event.type === "error") terminalError = true; onEvent(event as StreamEvent); } catch { onEvent({ type: "error", message: "Bản ghi SSE không thể đọc." }); } } };
    try { while (true) { const { done, value } = await reader.read(); buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done }); flush(); if (done) break; } if (!signal.aborted && !terminalDone && !terminalError) onEvent({ type: "error", message: "Luồng SSE đóng trước terminal done." }); } finally { reader.releaseLock(); }
  },
};
