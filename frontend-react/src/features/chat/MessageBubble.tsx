import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeHighlight from "rehype-highlight";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { Check, ChevronDown, Cloud, Copy, Flag, Lock, Pencil, Quote, RefreshCw, ShieldCheck, ThumbsDown, ThumbsUp, Wrench } from "lucide-react";
import { Badge, Spinner } from "@/components/ui";
import { cn } from "@/lib/utils";
import { DraftCard } from "./DraftCard";
import { MermaidBlock } from "./MermaidBlock";
import { downloadFile } from "@/api/client";
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
              {s.type === "plan" && <span>→ {s.plan?.join(" → ")}</span>}
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
  onReport?: (messageId: string) => void;
  onRegenerate?: (messageId: string) => void;
  onEdit?: (messageId: string, newText: string) => void;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  readOnly?: boolean;
}

// P1: copy an assistant answer to the clipboard, with a brief "copied" state.
function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      aria-label="sao chép"
      className="p-1 rounded hover:bg-muted text-muted-foreground"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setDone(true);
          setTimeout(() => setDone(false), 1500);
        } catch { /* clipboard blocked */ }
      }}
    >
      {done ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

// Biến marker [N] trong câu trả lời thành link #cite-N (bỏ qua [text](url) đã có).
function linkifyCitations(text: string): string {
  return text.replace(/\[(\d{1,3})\](?!\()/g, "[$1](#cite-$1)");
}

// Q3: tách phần có nguồn khỏi khối "kiến thức chung" gắn nhãn (ADR-0021) để render riêng biệt.
const WK_MARK = "--- Ngoài tài liệu BRAVO";
function splitWorldKnowledge(text: string): { grounded: string; world: string | null } {
  const idx = text.indexOf(WK_MARK);
  if (idx === -1) return { grounded: text, world: null };
  // Bỏ dòng nhãn khỏi phần world (đã hiển thị bằng badge), giữ nội dung sau nhãn.
  const after = text.slice(idx);
  const nl = after.indexOf("\n");
  return { grounded: text.slice(0, idx).trim(), world: nl === -1 ? "" : after.slice(nl + 1).trim() };
}

// Bấm vào nguồn #source-N: mở panel dẫn chứng + cuộn + nháy (harvest pattern DocsGPT, MIT).
function focusSource(n: number): void {
  setTimeout(() => {
    const el = document.getElementById(`source-${n}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
    el?.classList.add("cite-flash");
    setTimeout(() => el?.classList.remove("cite-flash"), 1600);
  }, 60);
}

export function MessageBubble({ m, onCite, onFeedback, onReport, onRegenerate, onEdit, onApprove, onReject, readOnly }: Props) {
  const isUser = m.role === "user";
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(m.content);
  const mdComponents = {
    // Khối ```mermaid -> render sơ đồ (thay cả <pre>); còn lại giữ <pre> mặc định.
    pre({ children, ...rest }: any) {
      const child = Array.isArray(children) ? children[0] : children;
      const cls: string = child?.props?.className || "";
      if (/language-mermaid/.test(cls)) {
        const raw = child.props.children;
        const text = Array.isArray(raw) ? raw.join("") : String(raw ?? "");
        return <MermaidBlock chart={text} />;
      }
      return <pre {...rest}>{children}</pre>;
    },
    a({ href, children, ...rest }: any) {
      const cite = /^#cite-(\d+)$/.exec(href || "");
      if (cite) {
        const n = Number(cite[1]);
        return (
          <a
            href={href}
            className="cite-ref"
            onClick={(e) => {
              e.preventDefault();
              if (m.citations?.length) onCite?.(m.citations);
              focusSource(n);
            }}
          >
            {children}
          </a>
        );
      }
      return <a href={href} target="_blank" rel="noreferrer" {...rest}>{children}</a>;
    },
  };
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div className={cn("max-w-[85%] rounded-lg px-4 py-2.5", isUser ? "bg-primary text-primary-foreground" : "bg-card border border-border shadow-card")}>
        {isUser && m.attachments && m.attachments.length > 0 && (
          <div className="mb-1.5 flex flex-wrap gap-1.5">
            {m.attachments.map((a, i) => (
              <span key={i} className="inline-flex items-center gap-1 rounded bg-primary-foreground/15 px-1.5 py-0.5 text-[11px]">
                {a.kind === "image" ? "🖼" : "📄"} {a.filename}
              </span>
            ))}
          </div>
        )}
        {!isUser && m.steps && <Steps steps={m.steps} />}
        {isUser && editing ? (
          <div className="min-w-[16rem]">
            <textarea
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="w-full rounded-md bg-primary-foreground/10 p-2 text-sm text-primary-foreground outline-none"
              rows={Math.min(8, Math.max(2, draft.split("\n").length))}
            />
            <div className="mt-1 flex justify-end gap-2 text-xs">
              <button className="opacity-80 hover:opacity-100" onClick={() => { setEditing(false); setDraft(m.content); }}>Huỷ</button>
              <button
                className="font-medium hover:underline"
                onClick={() => {
                  const t = draft.trim();
                  if (t && t !== m.content && m.id) onEdit?.(m.id, t);
                  setEditing(false);
                }}
              >Lưu & gửi lại</button>
            </div>
          </div>
        ) : (
        <div className={cn("prose-chat text-sm", isUser ? "text-primary-foreground" : "")}>
          {m.content ? (
            isUser ? (
              <Markdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex, rehypeHighlight]}>
                {m.content}
              </Markdown>
            ) : (() => {
              const { grounded, world } = splitWorldKnowledge(m.content);
              return (
                <>
                  {grounded && (
                    <Markdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex, rehypeHighlight]} components={mdComponents}>
                      {linkifyCitations(grounded)}
                    </Markdown>
                  )}
                  {world !== null && (
                    <div className="mt-3 rounded-md border border-dashed border-amber-400/60 bg-amber-50/50 dark:bg-amber-950/20 p-2.5">
                      <div className="mb-1 flex items-center gap-1 text-[11px] font-medium text-amber-700 dark:text-amber-400">
                        <Cloud className="h-3 w-3" /> Ngoài tài liệu BRAVO · kiến thức chung (chưa kiểm chứng)
                      </div>
                      <Markdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex, rehypeHighlight]}>
                        {world}
                      </Markdown>
                    </div>
                  )}
                </>
              );
            })()
          ) : m.streaming ? (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Spinner /> {m.statusText && <span className="text-xs">{m.statusText}</span>}
            </div>
          ) : null}
        </div>
        )}
        {isUser && !editing && m.id && onEdit && (
          <div className="mt-1 flex justify-end">
            <button aria-label="sửa câu hỏi" title="Sửa & gửi lại" className="p-1 rounded hover:bg-primary-foreground/15 text-primary-foreground/70" onClick={() => { setDraft(m.content); setEditing(true); }}>
              <Pencil className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
        {!isUser && m.draft?.payload && (
          <DraftCard payload={m.draft.payload as any} draftId={m.draft.draft_id} onApprove={onApprove} onReject={onReject} readOnly={readOnly} />
        )}
        {!isUser && !!m.artifacts?.length && (
          <div className="mt-2 flex flex-wrap gap-2">
            {m.artifacts.map((artifact) => (
              <button
                key={artifact.id}
                type="button"
                className="rounded border border-border px-2 py-1 text-xs text-primary hover:bg-muted"
                onClick={() => downloadFile(`/api/artifacts/${artifact.id}/download`, artifact.title)}
              >
                Tải {artifact.title}
              </button>
            ))}
          </div>
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
            <span className="ml-auto flex items-center gap-1">
              {m.id && onRegenerate && (
                <button aria-label="tạo lại câu trả lời" title="Tạo lại" className="p-1 rounded hover:bg-muted text-muted-foreground" onClick={() => onRegenerate(m.id!)}><RefreshCw className="h-3.5 w-3.5" /></button>
              )}
              {m.content && <CopyButton text={m.content} />}
              {m.id && onFeedback && (
                <>
                  <button aria-label="thích" className={cn("p-1 rounded hover:bg-muted", m.feedback === "like" && "text-success")} onClick={() => onFeedback(m.id!, "like")}><ThumbsUp className="h-3.5 w-3.5" /></button>
                  <button aria-label="không thích" className={cn("p-1 rounded hover:bg-muted", m.feedback === "dislike" && "text-destructive")} onClick={() => onFeedback(m.id!, "dislike")}><ThumbsDown className="h-3.5 w-3.5" /></button>
                </>
              )}
              {m.id && onReport && (
                <button aria-label="báo lỗi cho IT" title="Báo lỗi cho đội IT" className="p-1 rounded hover:bg-muted text-muted-foreground" onClick={() => onReport(m.id!)}><Flag className="h-3.5 w-3.5" /></button>
              )}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
