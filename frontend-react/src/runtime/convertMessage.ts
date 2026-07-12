import type { ThreadMessageLike } from "@assistant-ui/react";
import type { ChatMessage } from "@/api/types";

// P2: map our Zustand ChatMessage onto assistant-ui's ThreadMessageLike. Only `text` (and later
// `reasoning`) is sequence-ordered content; every layout-positioned BRAVO widget (DraftCard, the
// world-knowledge panel, citations, grounded/cloud badges, agent steps) rides in metadata.custom
// so the existing MessageBubble renderer can draw them unchanged.
export type BravoMeta = { chat: ChatMessage };

export function convertMessage(m: ChatMessage): ThreadMessageLike {
  const base = {
    id: m.id,
    createdAt: undefined,
    metadata: { custom: { chat: m } as BravoMeta },
  };
  if (m.role === "user") {
    return {
      ...base,
      role: "user",
      content: [{ type: "text", text: m.content }],
      attachments: (m.attachments ?? []).map((a, i) => ({
        id: `att-${i}`,
        type: a.kind === "image" ? "image" : "document",
        name: a.filename,
        contentType: a.kind === "image" ? "image/*" : "text/plain",
        status: { type: "complete" },
        content: [],
      })),
    };
  }
  return {
    ...base,
    role: "assistant",
    content: [{ type: "text", text: m.content || "" }],
    status: m.streaming ? { type: "running" } : { type: "complete", reason: "stop" },
  };
}
