import { authHeaders } from "./client";
import type { ConsultantProfile, SseEvent } from "./types";

// Stream một lượt chat qua POST + fetch ReadableStream (KHÔNG EventSource — bearer auth cần header).
// Parser rút gọn từ docsgpt _drainSseBody: chuẩn hoá CRLF, ranh giới \n\n, field data:.
export async function streamChat(
  conversationId: string,
  question: string,
  onEvent: (e: SseEvent) => void,
  signal: AbortSignal,
  attachmentIds: string[] = [],
  sourceIds: string[] = [],
  mode: "auto" | "deep_research" = "auto",
  consultantProfile: ConsultantProfile = "auto"
): Promise<void> {
  const res = await fetch(`/api/chat/${conversationId}/messages`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({
      question, attachment_ids: attachmentIds, source_ids: sourceIds, mode,
      consultant_profile: consultantProfile,
      // Selecting a visible profile asks for its scaffold, but the server-side global kill switch,
      // RLS, egress and approval policies remain authoritative.
      consultant_mode: consultantProfile === "auto" ? "auto" : "on",
    }),
    signal,
  });
  if (!res.ok || !res.body) {
    let msg = `Lỗi ${res.status}`;
    try {
      msg = (await res.json()).detail || msg;
    } catch {
      /* ignore */
    }
    onEvent({ type: "error", message: msg });
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n").replace(/\r/g, "\n");
      let idx: number;
      while ((idx = buf.indexOf("\n\n")) !== -1) {
        const record = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        for (const line of record.split("\n")) {
          if (line.startsWith(":")) continue; // comment/keepalive
          if (line.startsWith("data:")) {
            const data = line.slice(5).trim();
            if (!data) continue;
            try {
              onEvent(JSON.parse(data) as SseEvent);
            } catch {
              /* ignore malformed */
            }
          }
        }
      }
    }
  } finally {
    try {
      reader.releaseLock();
    } catch {
      /* ignore */
    }
  }
}
