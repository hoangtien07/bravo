import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { ChevronDown, Cloud, Lock, Quote, ShieldCheck, ThumbsDown, ThumbsUp, Wrench } from "lucide-react";
import { Badge, Spinner } from "@/components/ui";
import { cn } from "@/lib/utils";
import { DraftCard } from "./DraftCard";
import type { ChatMessage } from "@/api/types";

function Steps({ steps }: { steps: NonNullable<ChatMessage["steps"]> }) {
  const [open, setOpen] = useState(false);
  if (!steps.length) return null;
  return (
    <div className="my-1 text-xs">
      <button className="flex items-center gap-1 text-muted-foreground hover:text-foreground" onClick={() => setOpen(!open)}>
        <Wrench className="h-3 w-3" /> {steps.length} bước agent <ChevronDown className={cn("h-3 w-3 transition", open && "rotate-180")} />
      </button>
      {open && (
        <ul className="mt-1 ml-4 border-l border-border pl-2 space-y-0.5">
          {steps.map((s, i) => (
            <li key={i} className="text-muted-foreground">
              {s.type === "tool_call" && <span>🔧 gọi <b>{s.tool}</b></span>}
              {s.type === "tool_result" && <span>{s.isError ? "⚠" : "✓"} {s.tool}: {s.summary}</span>}
              {s.type === "step" && <span>· {s.action}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

interface Props {
  m: ChatMessage;
  onCite?: (citations: string[]) => void;
  onFeedback?: (messageId: string, v: "like" | "dislike") => void;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  readOnly?: boolean;
}

export function MessageBubble({ m, onCite, onFeedback, onApprove, onReject, readOnly }: Props) {
  const isUser = m.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div className={cn("max-w-[85%] rounded-lg px-4 py-2.5", isUser ? "bg-primary text-primary-foreground" : "bg-card border border-border shadow-card")}>
        {!isUser && m.steps && <Steps steps={m.steps} />}
        <div className={cn("prose-chat text-sm", isUser ? "text-primary-foreground" : "")}>
          {m.content ? <Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>{m.content}</Markdown> : m.streaming ? <Spinner /> : null}
        </div>
        {!isUser && m.draft?.payload && (
          <DraftCard payload={m.draft.payload as any} draftId={m.draft.draft_id} onApprove={onApprove} onReject={onReject} readOnly={readOnly} />
        )}
        {!isUser && !m.streaming && (
          <div className="flex items-center gap-2 mt-2 flex-wrap text-xs">
            {m.grounded !== undefined && (
              <Badge tone={m.grounded ? "ok" : "warn"}><ShieldCheck className="h-3 w-3" /> {m.grounded ? "đã kiểm chứng" : "chưa căn cứ"}</Badge>
            )}
            {m.routedCloud !== undefined && (
              <Badge tone="muted">{m.routedCloud ? <><Cloud className="h-3 w-3" /> cloud</> : <><Lock className="h-3 w-3" /> local</>}</Badge>
            )}
            {m.citations && m.citations.length > 0 && (
              <button className="inline-flex items-center gap-1 text-primary hover:underline" onClick={() => onCite?.(m.citations!)}>
                <Quote className="h-3 w-3" /> {m.citations.length} nguồn
              </button>
            )}
            {m.id && onFeedback && (
              <span className="ml-auto flex gap-1">
                <button aria-label="thích" className={cn("p-1 rounded hover:bg-muted", m.feedback === "like" && "text-success")} onClick={() => onFeedback(m.id!, "like")}><ThumbsUp className="h-3.5 w-3.5" /></button>
                <button aria-label="không thích" className={cn("p-1 rounded hover:bg-muted", m.feedback === "dislike" && "text-destructive")} onClick={() => onFeedback(m.id!, "dislike")}><ThumbsDown className="h-3.5 w-3.5" /></button>
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
