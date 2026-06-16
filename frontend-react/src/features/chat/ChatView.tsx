import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Share2, X } from "lucide-react";
import { api } from "@/api/client";
import { Button } from "@/components/ui";
import { useChat } from "@/store/chat";
import { MessageBubble } from "./MessageBubble";
import { Composer } from "./Composer";
import type { ChatMessage } from "@/api/types";

export function ChatView() {
  const { id } = useParams();
  const nav = useNavigate();
  const { conversationId, messages, sending, send, stop, setConversation, newConversation } = useChat();
  const [cites, setCites] = useState<string[] | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  // Load conversation theo URL (hoặc new khi vào "/").
  useEffect(() => {
    if (!id) {
      newConversation();
      return;
    }
    if (id === conversationId) return;
    api<{ id: string; title: string; messages: ChatMessage[] }>(`/api/conversations/${id}`)
      .then((d) => setConversation(id, d.messages))
      .catch(() => nav("/"));
  }, [id]);

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const onSend = (q: string) => {
    const wasNew = !id;
    send(q, () => {
      window.dispatchEvent(new Event("conv:refresh"));
      const cid = useChat.getState().conversationId;
      if (wasNew && cid) nav(`/c/${cid}`, { replace: true });
    });
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
  const feedback = async (mid: string, v: "like" | "dislike") => {
    if (!conversationId) return;
    await api(`/api/conversations/${conversationId}/messages/${mid}/feedback`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ value: v }),
    });
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
        <div className="flex-1 overflow-y-auto px-4 py-4">
          <div className="mx-auto max-w-3xl space-y-4">
            {!messages.length && (
              <div className="text-center text-muted-foreground mt-20">
                Hỏi tri thức nội bộ, số liệu tài chính, hoặc yêu cầu agent. Câu trả lời có dẫn chứng & kiểm chứng số.
              </div>
            )}
            {messages.map((m, i) => (
              <MessageBubble key={i} m={m} onCite={setCites} onFeedback={feedback} onApprove={approve} onReject={reject} />
            ))}
            <div ref={bottom} />
          </div>
        </div>
        <Composer onSend={onSend} sending={sending} onStop={stop} />
      </div>
      {cites && (
        <aside className="w-80 shrink-0 border-l border-border bg-card/60 overflow-y-auto">
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <span className="font-medium text-sm">Dẫn chứng</span>
            <button onClick={() => setCites(null)} aria-label="đóng"><X className="h-4 w-4" /></button>
          </div>
          <ul className="p-3 space-y-2">
            {cites.map((c, i) => (
              <li key={i} className="rounded-md border-l-2 border-primary bg-muted/50 px-2 py-1 text-xs">{c}</li>
            ))}
          </ul>
        </aside>
      )}
    </div>
  );
}
