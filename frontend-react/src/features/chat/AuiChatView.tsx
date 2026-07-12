import { createContext, useContext, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AssistantRuntimeProvider, ThreadPrimitive, useMessage } from "@assistant-ui/react";
import { ArrowDown, Share2, X } from "lucide-react";
import { api } from "@/api/client";
import { Button } from "@/components/ui";
import { useChat } from "@/store/chat";
import { useBravoRuntime } from "@/runtime/bravoRuntime";
import type { BravoMeta } from "@/runtime/convertMessage";
import { MessageBubble } from "./MessageBubble";
import { Composer } from "./Composer";
import type { ChatMessage } from "@/api/types";

// Handlers shared with the message components rendered inside <ThreadPrimitive.Messages>.
interface Handlers {
  onCite: (c: string[]) => void;
  feedback: (id: string, v: "like" | "dislike") => void;
  report: (id: string) => void;
  regenerate: (id: string) => void;
  edit: (id: string, text: string) => void;
  approve: (id: string) => void;
  reject: (id: string) => void;
  lastId?: string;
}
const HandlersCtx = createContext<Handlers | null>(null);

function BubbleFromMeta() {
  const chat = useMessage((m) => (m.metadata?.custom as BravoMeta | undefined)?.chat) as
    | ChatMessage
    | undefined;
  const h = useContext(HandlersCtx);
  if (!chat || !h) return null;
  return (
    <MessageBubble
      m={chat}
      onCite={h.onCite}
      onFeedback={h.feedback}
      onReport={h.report}
      onRegenerate={chat.id && chat.id === h.lastId ? h.regenerate : undefined}
      onEdit={h.edit}
      onApprove={h.approve}
      onReject={h.reject}
    />
  );
}

export function AuiChatView() {
  const { id } = useParams();
  const nav = useNavigate();
  const { conversationId, messages, sending, send, stop, setConversation, newConversation,
          staged, attach, removeAttachment, addMessage } = useChat();
  const runtime = useBravoRuntime();
  const [cites, setCites] = useState<string[] | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const atBottom = useRef(true);
  const [showJump, setShowJump] = useState(false);

  useEffect(() => {
    if (!id) { newConversation(); return; }
    if (id === conversationId) return;
    api<{ id: string; title: string; messages: ChatMessage[] }>(`/api/conversations/${id}`)
      .then((d) => setConversation(id, d.messages)).catch(() => nav("/"));
  }, [id]);

  useEffect(() => {
    if (atBottom.current) scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  const onScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
    atBottom.current = dist < 80;
    setShowJump(!atBottom.current);
  };
  const jump = () => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    atBottom.current = true; setShowJump(false);
  };

  const onSend = (q: string) => {
    const wasNew = !id;
    send(q, () => {
      window.dispatchEvent(new Event("conv:refresh"));
      const cid = useChat.getState().conversationId;
      if (wasNew && cid) nav(`/c/${cid}`, { replace: true });
    });
  };
  const onUploadInvoice = async (files: FileList | File[]) => {
    for (const f of Array.from(files)) {
      const fd = new FormData(); fd.append("file", f);
      try {
        const draft = await (await fetch("/api/invoices/draft", {
          method: "POST", headers: { Authorization: `Bearer ${sessionStorage.getItem("bravo_token")}` },
          body: fd,
        })).json();
        addMessage({ role: "assistant", content: "", draft });
      } catch { /* surfaced by the draft card absence */ }
    }
  };

  const patchFeedback = (id2: string, v: "like" | "dislike" | null) =>
    useChat.setState((s) => ({ messages: s.messages.map((m) => (m.id === id2 ? { ...m, feedback: v } : m)) }));
  const handlers: Handlers = {
    onCite: setCites,
    feedback: async (mid, v) => {
      if (!conversationId) return;
      const next = messages.find((m) => m.id === mid)?.feedback === v ? null : v;
      patchFeedback(mid, next);
      await api(`/api/conversations/${conversationId}/messages/${mid}/feedback`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ value: next }),
      }).catch(() => patchFeedback(mid, next === v ? null : v));
    },
    report: async (mid) => {
      if (!conversationId) return;
      const comment = window.prompt("Mô tả vấn đề để gửi đội IT:", "");
      if (comment === null) return;
      patchFeedback(mid, "dislike");
      await api(`/api/conversations/${conversationId}/messages/${mid}/feedback`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: "dislike", comment, category: "other" }),
      }).then(() => alert("Đã gửi báo cáo. Cảm ơn bạn!")).catch(() => {});
    },
    regenerate: async (assistantId) => {
      if (!conversationId || sending) return;
      const idx = messages.findIndex((m) => m.id === assistantId);
      if (idx < 1) return;
      const userMsg = messages[idx - 1];
      if (userMsg.role !== "user" || !userMsg.id) return;
      await api(`/api/conversations/${conversationId}/truncate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ from_message_id: userMsg.id, inclusive: true }),
      }).catch(() => {});
      useChat.setState((s) => ({ messages: s.messages.slice(0, idx - 1) }));
      onSend(userMsg.content);
    },
    edit: async (userMessageId, newText) => {
      if (!conversationId || sending) return;
      const idx = messages.findIndex((m) => m.id === userMessageId);
      if (idx < 0) return;
      await api(`/api/conversations/${conversationId}/truncate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ from_message_id: userMessageId, inclusive: true }),
      }).catch(() => {});
      useChat.setState((s) => ({ messages: s.messages.slice(0, idx) }));
      onSend(newText);
    },
    approve: async (did) => { try { await api(`/api/drafts/${did}/approve`, { method: "POST" }); alert("Đã duyệt."); } catch (e) { alert(e instanceof Error ? e.message : "Lỗi"); } },
    reject: async (did) => { const r = window.prompt("Lý do từ chối?", "Cần sửa"); if (r === null) return; await api(`/api/drafts/${did}/reject`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason: r }) }); },
    lastId: messages[messages.length - 1]?.id,
  };
  const share = async () => {
    if (!conversationId) return;
    const { url } = await api<{ url: string }>(`/api/conversations/${conversationId}/share`, { method: "POST" });
    await navigator.clipboard?.writeText(window.location.origin + url).catch(() => {});
    alert("Đã sao chép liên kết chia sẻ: " + url);
  };

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="flex flex-1 min-h-0">
        <div className="flex-1 flex flex-col min-w-0">
          <header className="flex items-center justify-between border-b border-border px-4 py-2">
            <h1 className="font-semibold tracking-tight">BRAVO AI Copilot <span className="text-xs text-muted-foreground">· beta</span></h1>
            {id && <Button variant="ghost" size="sm" onClick={share}><Share2 className="h-4 w-4" /> Chia sẻ</Button>}
          </header>
          <div ref={scrollRef} onScroll={onScroll} className="relative flex-1 overflow-y-auto px-4 py-4">
            <ThreadPrimitive.Root>
              <div className="mx-auto max-w-3xl space-y-4">
                {!messages.length && (
                  <div className="text-center text-muted-foreground mt-20">
                    Hỏi tri thức nội bộ, số liệu tài chính, hoặc yêu cầu agent. Câu trả lời có dẫn chứng & kiểm chứng số.
                  </div>
                )}
                <HandlersCtx.Provider value={handlers}>
                  <ThreadPrimitive.Messages components={{ UserMessage: BubbleFromMeta, AssistantMessage: BubbleFromMeta }} />
                </HandlersCtx.Provider>
              </div>
            </ThreadPrimitive.Root>
            {showJump && (
              <button onClick={jump} aria-label="Xuống cuối" className="sticky bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-1 rounded-full border border-border bg-card px-3 py-1.5 text-xs shadow-card hover:bg-muted">
                <ArrowDown className="h-3.5 w-3.5" /> Xuống cuối
              </button>
            )}
          </div>
          <Composer onSend={onSend} sending={sending} onStop={stop} staged={staged} onAttach={attach} onRemoveAttach={removeAttachment} onUploadInvoice={onUploadInvoice} />
        </div>
        {cites && (
          <aside className="w-80 shrink-0 border-l border-border bg-card/60 overflow-y-auto">
            <div className="flex items-center justify-between border-b border-border px-3 py-2">
              <span className="font-medium text-sm">Dẫn chứng</span>
              <button onClick={() => setCites(null)} aria-label="đóng"><X className="h-4 w-4" /></button>
            </div>
            <ol className="p-3 space-y-2 text-sm">
              {cites.map((c, i) => (
                <li key={i} id={`source-${i + 1}`} className="rounded border border-border bg-card p-2">
                  <span className="cite-num">[{i + 1}]</span> {c}
                </li>
              ))}
            </ol>
          </aside>
        )}
      </div>
    </AssistantRuntimeProvider>
  );
}
