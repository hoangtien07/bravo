import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowDown, Share2, X } from "lucide-react";
import { api, authHeaders } from "@/api/client";
import { Button } from "@/components/ui";
import { useChat } from "@/store/chat";
import { MessageBubble } from "./MessageBubble";
import { Composer } from "./Composer";
import { ConsultantWorkflowStrip } from "./ConsultantWorkflowStrip";
import type { ChatMessage } from "@/api/types";

export function ChatView() {
  const { id } = useParams();
  const nav = useNavigate();
  const { conversationId, messages, sending, send, stop, setConversation, newConversation, addMessage, staged, attach, removeAttachment, consultantState, refreshConsultantState, submitConsultantFeedback } = useChat();
  const [cites, setCites] = useState<string[] | null>(null);
  const [uploading, setUploading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const atBottomRef = useRef(true);
  const [showJump, setShowJump] = useState(false);

  // Load conversation theo URL (hoặc new khi vào "/").
  useEffect(() => {
    atBottomRef.current = true;
    setShowJump(false);
    if (!id) {
      newConversation();
      return;
    }
    if (id === conversationId) {
      void refreshConsultantState(id);
      return;
    }
    api<{ id: string; title: string; messages: ChatMessage[] }>(`/api/conversations/${id}`)
      .then((d) => {
        setConversation(id, d.messages);
        void useChat.getState().refreshConsultantState(id);
      })
      .catch(() => nav("/"));
  }, [id]);

  // Auto-scroll THÔNG MINH: chỉ kéo xuống nếu người dùng đang ở đáy (không phá khi đọc lại trên).
  const onScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
    atBottomRef.current = dist < 80;
    setShowJump(!atBottomRef.current);
  };
  const jumpToBottom = () => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    atBottomRef.current = true;
    setShowJump(false);
  };
  useEffect(() => {
    if (atBottomRef.current) scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  const onSend = (q: string) => {
    const wasNew = !id;
    send(q, () => {
      window.dispatchEvent(new Event("conv:refresh"));
      const cid = useChat.getState().conversationId;
      if (wasNew && cid) nav(`/c/${cid}`, { replace: true });
    });
  };

  // Hoá đơn XML thả vào khung chat -> bút toán nháp (kiểm Nợ=Có, map TT99). Tài liệu/ảnh khác
  // đi qua đính-kèm-tin-nhắn (store.attach) — xem Composer.
  const onUploadInvoice = async (files: FileList | File[]) => {
    if (!files || !Array.from(files).length) return;
    if (!conversationId) newConversation();
    setUploading(true);
    for (const f of Array.from(files)) {
      const fd = new FormData();
      fd.append("file", f);
      try {
        const r = await fetch("/api/invoices/draft", { method: "POST", headers: authHeaders(), body: fd });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || `Lỗi ${r.status}`);
        addMessage({
          role: "assistant",
          content: `📎 Đã nạp hoá đơn **${f.name}** → bút toán nháp (kiểm Nợ=Có, map TT99):`,
          draft: { draft_id: d.draft_id, kind: d.kind, payload: d.journal },
        });
      } catch (e) {
        addMessage({ role: "assistant", content: `⚠ Không nạp được **${f.name}**: ${e instanceof Error ? e.message : "lỗi"}` });
      }
    }
    setUploading(false);
    window.dispatchEvent(new Event("conv:refresh"));
    const cid = useChat.getState().conversationId;
    if (!id && cid) nav(`/c/${cid}`, { replace: true });
  };

  const approve = async (did: string) => {
    try {
      await api(`/api/drafts/${did}/approve`, { method: "POST" });
      alert("Đã duyệt bút toán.");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Lỗi duyệt");
    }
  };
  const reject = async (did: string) => {
    const reason = prompt("Lý do từ chối?", "Cần sửa");
    if (reason === null) return;
    await api(`/api/drafts/${did}/reject`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason }) });
  };
  const patchFeedback = (mid: string, v: "like" | "dislike" | null) =>
    useChat.setState((s) => ({ messages: s.messages.map((m) => (m.id === mid ? { ...m, feedback: v } : m)) }));

  const feedback = async (mid: string, v: "like" | "dislike") => {
    if (!conversationId) return;
    const next = messages.find((m) => m.id === mid)?.feedback === v ? null : v;
    patchFeedback(mid, next);   // optimistic
    await api(`/api/conversations/${conversationId}/messages/${mid}/feedback`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ value: next }),
    }).catch(() => patchFeedback(mid, next === v ? null : v));   // revert on failure
  };
  // P1: report a bad answer to the IT team (free-text + category), reuses the feedback endpoint.
  const report = async (mid: string) => {
    if (!conversationId) return;
    const comment = window.prompt("Mô tả vấn đề để gửi đội IT cải thiện phần mềm:", "");
    if (comment === null) return;
    patchFeedback(mid, "dislike");
    await api(`/api/conversations/${conversationId}/messages/${mid}/feedback`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value: "dislike", comment, category: "other" }),
    }).then(() => alert("Đã gửi báo cáo cho đội IT. Cảm ơn bạn!"))
      .catch((e) => alert(e instanceof Error ? e.message : "Không gửi được báo cáo"));
  };
  // P3: regenerate — drop this turn (user question + its answer) and re-run the same question.
  const regenerate = async (assistantId: string) => {
    if (!conversationId || sending) return;
    const idx = messages.findIndex((m) => m.id === assistantId);
    if (idx < 1) return;
    const userMsg = messages[idx - 1];
    if (userMsg.role !== "user" || !userMsg.id) return;
    try {
      await api(`/api/conversations/${conversationId}/truncate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ from_message_id: userMsg.id, inclusive: true }),
      });
    } catch (e) {
      alert(e instanceof Error ? e.message : "Không tạo lại được câu trả lời");
      return;
    }
    useChat.setState((s) => ({ messages: s.messages.slice(0, idx - 1) })); // drop the old turn
    onSend(userMsg.content);   // re-run (BE re-persists the user turn fresh)
  };
  // P3: edit a user question — truncate from that turn (inclusive) and re-run with the new text.
  const edit = async (userMessageId: string, newText: string) => {
    if (!conversationId || sending) return;
    const idx = messages.findIndex((m) => m.id === userMessageId);
    if (idx < 0) return;
    try {
      await api(`/api/conversations/${conversationId}/truncate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ from_message_id: userMessageId, inclusive: true }),
      });
    } catch (e) {
      alert(e instanceof Error ? e.message : "Không sửa được câu hỏi");
      return;
    }
    useChat.setState((s) => ({ messages: s.messages.slice(0, idx) }));
    onSend(newText);
  };
  const share = async () => {
    if (!conversationId) return;
    const { url } = await api<{ url: string }>(`/api/conversations/${conversationId}/share`, { method: "POST" });
    await navigator.clipboard?.writeText(window.location.origin + url).catch(() => {});
    alert("Đã sao chép liên kết chia sẻ: " + url);
  };

  return (
    <div className="flex flex-1 min-h-0">
      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex items-center justify-between border-b border-border px-4 py-2">
          <h1 className="font-semibold tracking-tight">BRAVO AI Copilot</h1>
          {id && <Button variant="ghost" size="sm" onClick={share}><Share2 className="h-4 w-4" /> Chia sẻ</Button>}
        </header>
        <ConsultantWorkflowStrip state={consultantState} onFeedback={submitConsultantFeedback} />
        <div ref={scrollRef} onScroll={onScroll} className="relative flex-1 overflow-y-auto px-4 py-4">
          <div className="mx-auto max-w-3xl space-y-4">
            {!messages.length && (
              <div className="text-center text-muted-foreground mt-20">
                Hỏi tri thức nội bộ, số liệu tài chính, hoặc yêu cầu agent. Câu trả lời có dẫn chứng & kiểm chứng số.
              </div>
            )}
            {messages.map((m, i) => (
              <MessageBubble key={i} m={m} onCite={setCites} onFeedback={feedback} onReport={report} onRegenerate={i === messages.length - 1 ? regenerate : undefined} onEdit={edit} onApprove={approve} onReject={reject} />
            ))}
          </div>
          {showJump && (
            <button
              onClick={jumpToBottom}
              aria-label="Xuống cuối"
              className="sticky bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-1 rounded-full border border-border bg-card px-3 py-1.5 text-xs shadow-card hover:bg-muted"
            >
              <ArrowDown className="h-3.5 w-3.5" /> Xuống cuối
            </button>
          )}
        </div>
        <Composer
          onSend={onSend}
          sending={sending || uploading}
          onStop={stop}
          staged={staged}
          onAttach={attach}
          onRemoveAttach={removeAttachment}
          onUploadInvoice={onUploadInvoice}
        />
      </div>
      {cites && (
        <aside className="w-80 shrink-0 border-l border-border bg-card/60 overflow-y-auto">
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <span className="font-medium text-sm">Dẫn chứng</span>
            <button onClick={() => setCites(null)} aria-label="đóng"><X className="h-4 w-4" /></button>
          </div>
          <ul className="p-3 space-y-2">
            {cites.map((c, i) => (
              <li
                key={i}
                id={`source-${i + 1}`}
                className="flex items-start rounded-md border-l-2 border-primary bg-muted/50 px-2 py-1.5 text-xs"
              >
                <span className="cite-num">{i + 1}</span>
                <span className="min-w-0 break-words">{c}</span>
              </li>
            ))}
          </ul>
        </aside>
      )}
    </div>
  );
}
