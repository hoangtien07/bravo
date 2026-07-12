import { useExternalStoreRuntime, type AppendMessage } from "@assistant-ui/react";
import { api } from "@/api/client";
import { useChat } from "@/store/chat";
import { convertMessage } from "./convertMessage";

// P2: an ExternalStoreRuntime backed by the existing Zustand chat store — assistant-ui becomes the
// Thread shell/runtime while the store stays the single source of truth (streaming, attachments,
// edit/regenerate all still flow through it). Behind a feature flag; the legacy ChatView is default.
export function useBravoRuntime() {
  const messages = useChat((s) => s.messages);
  const sending = useChat((s) => s.sending);

  const textOf = (m: AppendMessage) =>
    m.content.filter((c) => c.type === "text").map((c) => (c as { text: string }).text).join("");

  const truncate = async (fromMessageId: string) => {
    const cid = useChat.getState().conversationId;
    if (!cid) return;
    await api(`/api/conversations/${cid}/truncate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ from_message_id: fromMessageId, inclusive: true }),
    });
  };

  return useExternalStoreRuntime({
    messages,
    isRunning: sending,
    convertMessage,
    onNew: async (m: AppendMessage) => {
      const t = textOf(m).trim();
      if (t) await useChat.getState().send(t);
    },
    // Edit a user turn: truncate from it, drop locally, re-run with the new text.
    onEdit: async (m: AppendMessage) => {
      const parentId = m.parentId;   // the user message being edited keeps its id via parentId chain
      const msgs = useChat.getState().messages;
      const idx = parentId ? msgs.findIndex((x) => x.id === parentId) : msgs.length;
      const target = idx >= 0 ? msgs[idx] : undefined;
      const editId = target?.id;
      const t = textOf(m).trim();
      if (!editId || !t) return;
      await truncate(editId);
      useChat.setState((s) => ({ messages: s.messages.slice(0, idx) }));
      await useChat.getState().send(t);
    },
    // Regenerate: re-run the user turn that produced the assistant message at `parentId`.
    onReload: async (parentId: string | null) => {
      const msgs = useChat.getState().messages;
      const aIdx = parentId ? msgs.findIndex((x) => x.id === parentId) : msgs.length - 1;
      // parentId is the assistant message id; the user turn is the one before it.
      const uIdx = aIdx > 0 ? aIdx - 1 : msgs.findIndex((x) => x.role === "user");
      const userMsg = msgs[uIdx];
      if (!userMsg || userMsg.role !== "user" || !userMsg.id) return;
      await truncate(userMsg.id);
      useChat.setState((s) => ({ messages: s.messages.slice(0, uIdx) }));
      await useChat.getState().send(userMsg.content);
    },
    onCancel: async () => useChat.getState().stop(),
    adapters: {
      feedback: {
        submit: ({ message, type }) => {
          const cid = useChat.getState().conversationId;
          if (!cid || !message.id) return;
          void api(`/api/conversations/${cid}/messages/${message.id}/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ value: type === "positive" ? "like" : "dislike" }),
          }).catch(() => {});
        },
      },
    },
  });
}
