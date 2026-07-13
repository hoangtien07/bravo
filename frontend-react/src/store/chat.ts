import { create } from "zustand";
import { streamChat } from "@/api/sse";
import { uploadAttachment, deleteAttachment, getAttachment } from "@/api/workspace";
import type { AgentStep, ChatMessage, SourceItem, StagedAttachment } from "@/api/types";

function uuid() {
  return crypto.randomUUID();
}

function kindOf(file: File): "image" | "text" {
  return file.type.startsWith("image/") ? "image" : "text";
}

interface ChatState {
  conversationId: string | null;
  messages: ChatMessage[];
  sending: boolean;
  abort: AbortController | null;
  staged: StagedAttachment[];
  runMode: "auto" | "deep_research";
  pinnedSources: SourceItem[];   // P4-lite: workspace docs ghim vào ngữ cảnh hội thoại
  newConversation: () => string;
  setConversation: (id: string, messages: ChatMessage[]) => void;
  addMessage: (m: ChatMessage) => void;
  attach: (files: FileList | File[]) => Promise<void>;
  removeAttachment: (localId: string) => void;
  pinSource: (s: SourceItem) => void;
  unpinSource: (id: string) => void;
  setRunMode: (mode: "auto" | "deep_research") => void;
  send: (question: string, onDone?: () => void) => Promise<void>;
  stop: () => void;
}

export const useChat = create<ChatState>((set, get) => ({
  conversationId: null,
  messages: [],
  sending: false,
  abort: null,
  staged: [],
  runMode: "auto",
  pinnedSources: [],

  pinSource: (s) => set((st) => st.pinnedSources.some((x) => x.id === s.id)
    ? st : { pinnedSources: [...st.pinnedSources, s] }),
  unpinSource: (id) => set((st) => ({ pinnedSources: st.pinnedSources.filter((x) => x.id !== id) })),
  setRunMode: (runMode) => set({ runMode }),

  newConversation: () => {
    const id = uuid();
    set({ conversationId: id, messages: [], staged: [], pinnedSources: [] });
    return id;
  },

  setConversation: (id, messages) => set({ conversationId: id, messages, staged: [], pinnedSources: [] }),

  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),

  attach: async (files) => {
    const list = Array.from(files);
    const patch = (localId: string, fn: (a: StagedAttachment) => void) =>
      set((s) => ({
        staged: s.staged.map((a) => {
          if (a.localId !== localId) return a;
          const next = { ...a };
          fn(next);
          return next;
        }),
      }));
    for (const file of list) {
      const localId = uuid();
      const kind = kindOf(file);
      const entry: StagedAttachment = {
        localId,
        name: file.name,
        kind,
        status: "uploading",
        previewUrl: kind === "image" ? URL.createObjectURL(file) : undefined,
      };
      set((s) => ({ staged: [...s.staged, entry] }));
      try {
        const att = await uploadAttachment(file);
        patch(localId, (a) => {
          a.id = att.id;
          a.status = att.status;
          a.error = att.error || undefined;
        });
        // RC-FE3: docx/pdf extract asynchronously (worker). Poll until ready/failed so the
        // attachment is never silently stuck "pending". (Images/small text return "ready" inline.)
        if (att.status === "pending") void pollUntilReady(att.id, localId);
      } catch (e) {
        patch(localId, (a) => {
          a.status = "failed";
          a.error = e instanceof Error ? e.message : "Tải lên thất bại";
        });
      }
    }

    async function pollUntilReady(id: string, lid: string) {
      const deadline = Date.now() + 60_000;
      let delay = 1500;
      while (Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, delay));
        delay = Math.min(delay + 1000, 5000);
        const cur = get().staged.find((a) => a.localId === lid);
        if (!cur || cur.status === "ready" || cur.status === "failed") return; // removed/resolved
        try {
          const att = await getAttachment(id);
          if (att.status !== "pending") {
            patch(lid, (a) => {
              a.status = att.status;
              a.error = att.error || undefined;
            });
            return;
          }
        } catch {
          /* transient network error — keep polling until the deadline */
        }
      }
      patch(lid, (a) => {
        if (a.status === "pending") {
          a.status = "failed";
          a.error = "Xử lý tệp quá lâu (worker chưa chạy?)";
        }
      });
    }
  },

  removeAttachment: (localId) =>
    set((s) => {
      const a = s.staged.find((x) => x.localId === localId);
      if (a?.previewUrl) URL.revokeObjectURL(a.previewUrl);
      if (a?.id) void deleteAttachment(a.id).catch(() => {});
      return { staged: s.staged.filter((x) => x.localId !== localId) };
    }),

  stop: () => {
    get().abort?.abort();
    set({ sending: false, abort: null });
  },

  send: async (question, onDone) => {
    // Snapshot staged attachments BEFORE newConversation() (which wipes staged:[]) — RC-FE2.
    // Reading after the wipe silently dropped first-turn attachments.
    const stagedNow = get().staged;
    const ready = stagedNow.filter((a) => a.status === "ready" && a.id);
    const attachmentIds = ready.map((a) => a.id!) as string[];
    const sentAttachments = ready.map((a) => ({ filename: a.name, kind: a.kind }));
    const sourceIds = get().pinnedSources.map((s) => s.id);   // P4-lite: pinned workspace docs
    const mode = get().runMode;

    let cid = get().conversationId;
    if (!cid) cid = get().newConversation();
    const ac = new AbortController();
    // Release image preview URLs now that the turn is sent.
    stagedNow.forEach((a) => a.previewUrl && URL.revokeObjectURL(a.previewUrl));
    // optimistic: user message (with attachments) + assistant placeholder (streaming)
    set((s) => ({
      sending: true,
      abort: ac,
      staged: [],
      messages: [
        ...s.messages,
        { role: "user", content: question, attachments: sentAttachments },
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
          case "attachments":
            // Backend echoes what it actually consumed (incl. re-injected prior text files).
            break;
          case "status":
            patchLast((m) => (m.statusText = e.text));
            break;
          case "plan":
          case "plan_update":
            patchLast((m) => {
              const prior = m.steps || [];
              const nextPlan: AgentStep = { type: "plan", plan: e.steps };
              const lastPlan = [...prior].map((s, i) => ({ s, i })).reverse().find(({ s }) => s.type === "plan");
              m.steps = lastPlan
                ? prior.map((s, i) => i === lastPlan.i ? nextPlan : s)
                : [...prior, nextPlan];
            });
            break;
          case "artifact":
            patchLast((m) => (m.artifacts = [...(m.artifacts || []), {
              id: e.artifact_id, kind: e.kind, title: e.title,
            }]));
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
            set((s) => {
              const msgs = s.messages.slice();
              const last = msgs.length - 1;
              if (last >= 0) {
                msgs[last] = {
                  ...msgs[last], streaming: false, grounded: e.grounded,
                  routedCloud: e.routed_cloud, clarify: e.clarify, statusText: undefined,
                  ...(e.message_id ? { id: e.message_id } : {}),        // enables like/dislike now
                  ...(e.citations ? { citations: e.citations } : {}),   // pruned citations
                };
              }
              // Also stamp the user turn's id (needed to truncate/regenerate from it).
              if (last - 1 >= 0 && e.user_message_id && msgs[last - 1].role === "user") {
                msgs[last - 1] = { ...msgs[last - 1], id: e.user_message_id };
              }
              return { messages: msgs };
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
      ac.signal,
      attachmentIds,
      sourceIds,
      mode
    );
    set({ sending: false, abort: null });
    onDone?.();
  },
}));
