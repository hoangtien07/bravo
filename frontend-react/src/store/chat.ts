import { create } from "zustand";
import { streamChat } from "@/api/sse";
import type { ChatMessage } from "@/api/types";

function uuid() {
  return crypto.randomUUID();
}

interface ChatState {
  conversationId: string | null;
  messages: ChatMessage[];
  sending: boolean;
  abort: AbortController | null;
  newConversation: () => string;
  setConversation: (id: string, messages: ChatMessage[]) => void;
  addMessage: (m: ChatMessage) => void;
  send: (question: string, onDone?: () => void) => Promise<void>;
  stop: () => void;
}

export const useChat = create<ChatState>((set, get) => ({
  conversationId: null,
  messages: [],
  sending: false,
  abort: null,

  newConversation: () => {
    const id = uuid();
    set({ conversationId: id, messages: [] });
    return id;
  },

  setConversation: (id, messages) => set({ conversationId: id, messages }),

  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),

  stop: () => {
    get().abort?.abort();
    set({ sending: false, abort: null });
  },

  send: async (question, onDone) => {
    let cid = get().conversationId;
    if (!cid) cid = get().newConversation();
    const ac = new AbortController();
    // optimistic: user message + assistant placeholder (streaming)
    set((s) => ({
      sending: true,
      abort: ac,
      messages: [
        ...s.messages,
        { role: "user", content: question },
        { role: "assistant", content: "", streaming: true, steps: [], citations: [], draft: null },
      ],
    }));

    const patchLast = (fn: (m: ChatMessage) => void) =>
      set((s) => {
        const msgs = s.messages.slice();
        const last = { ...msgs[msgs.length - 1] };
        fn(last);
        msgs[msgs.length - 1] = last;
        return { messages: msgs };
      });

    await streamChat(
      cid,
      question,
      (e) => {
        switch (e.type) {
          case "source":
            patchLast((m) => (m.citations = e.citations));
            break;
          case "step":
            patchLast((m) => (m.steps = [...(m.steps || []), { type: "step", action: e.action }]));
            break;
          case "tool_call":
            patchLast((m) => (m.steps = [...(m.steps || []), { type: "tool_call", tool: e.tool, args: e.args }]));
            break;
          case "tool_result":
            patchLast((m) => (m.steps = [...(m.steps || []), { type: "tool_result", tool: e.tool, isError: e.isError, summary: e.summary }]));
            break;
          case "draft":
            patchLast((m) => (m.draft = { draft_id: e.draft_id, kind: e.kind, payload: e.payload }));
            break;
          case "answer":
            patchLast((m) => (m.content += e.delta));
            break;
          case "done":
            patchLast((m) => {
              m.streaming = false;
              m.grounded = e.grounded;
              m.routedCloud = e.routed_cloud;
              m.clarify = e.clarify;
            });
            break;
          case "error":
            patchLast((m) => {
              m.streaming = false;
              m.content = (m.content || "") + `\n\n⚠ ${e.message}`;
            });
            break;
        }
      },
      ac.signal
    );
    set({ sending: false, abort: null });
    onDone?.();
  },
}));
