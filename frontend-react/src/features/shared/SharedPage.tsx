import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { MessageBubble } from "@/features/chat/MessageBubble";
import type { ChatMessage } from "@/api/types";

// Xem hội thoại chia sẻ read-only (không auth, tra theo token).
export function SharedPage() {
  const { token } = useParams();
  const [data, setData] = useState<{ title: string; messages: ChatMessage[] } | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    fetch(`/api/shared/${token}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("Liên kết không hợp lệ"))))
      .then(setData)
      .catch((e) => setErr(e.message));
  }, [token]);

  if (err) return <div className="grid place-items-center h-screen text-muted-foreground">{err}</div>;
  if (!data) return <div className="grid place-items-center h-screen text-muted-foreground">Đang tải…</div>;

  return (
    <div className="min-h-screen">
      <header className="border-b border-border px-4 py-3">
        <h1 className="font-semibold">{data.title}</h1>
        <p className="text-xs text-muted-foreground">Hội thoại chia sẻ (chỉ đọc) · BRAVO AI Copilot</p>
      </header>
      <div className="mx-auto max-w-3xl p-4 space-y-4">
        {data.messages.map((m, i) => (
          <MessageBubble key={i} m={m} readOnly />
        ))}
      </div>
    </div>
  );
}
