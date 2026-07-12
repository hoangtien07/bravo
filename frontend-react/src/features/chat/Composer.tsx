import { useEffect, useRef, useState } from "react";
import { Paperclip, Send, Square, X, FileText, Loader2 } from "lucide-react";
import { Button, Textarea } from "@/components/ui";
import { cn } from "@/lib/utils";
import type { StagedAttachment } from "@/api/types";

interface Props {
  onSend: (q: string) => void;
  sending: boolean;
  onStop: () => void;
  staged: StagedAttachment[];
  onAttach: (files: FileList | File[]) => void | Promise<void>;
  onRemoveAttach: (localId: string) => void;
  onUploadInvoice?: (files: FileList | File[]) => void | Promise<void>; // XML -> journal draft
}

const ATTACH_ACCEPT = ".png,.jpg,.jpeg,.webp,.gif,.txt,.md,.markdown,.docx,.pdf,image/*";

export function Composer({ onSend, sending, onStop, staged, onAttach, onRemoveAttach, onUploadInvoice }: Props) {
  const [text, setText] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  // Autosize: grow with content up to ~10 rows, then scroll inside.
  const autosize = () => {
    const el = taRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 240) + "px";
  };
  useEffect(() => { autosize(); }, [text]);

  // Fail LOUD: never let a turn be sent while an attachment is still processing or has failed —
  // otherwise the file is silently dropped and the answer is wrong for lack of context (RC-FE1).
  const anyProcessing = staged.some((a) => a.status === "uploading" || a.status === "pending");
  const anyFailed = staged.some((a) => a.status === "failed");
  const blockSend = anyProcessing || anyFailed;

  const submit = () => {
    const q = text.trim();
    if (!q || sending || blockSend) return;
    onSend(q);
    setText("");
  };

  // Split dropped files: XML invoices go to the draft flow; everything else becomes an attachment.
  const routeFiles = (files: FileList | File[]) => {
    const arr = Array.from(files);
    const xml = arr.filter((f) => /\.xml$/i.test(f.name) || f.type.includes("xml"));
    const rest = arr.filter((f) => !(/\.xml$/i.test(f.name) || f.type.includes("xml")));
    if (xml.length && onUploadInvoice) void onUploadInvoice(xml);
    if (rest.length) void onAttach(rest);
  };

  return (
    <div
      className={cn("border-t border-border bg-background p-3", dragOver && "ring-2 ring-primary ring-inset")}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { e.preventDefault(); setDragOver(false); routeFiles(e.dataTransfer.files); }}
    >
      {staged.length > 0 && (
        <div className="mx-auto max-w-3xl mb-2 flex flex-wrap gap-2">
          {staged.map((a) => (
            <div key={a.localId} className="relative flex items-center gap-2 rounded-md border border-border bg-card px-2 py-1 text-xs">
              {a.kind === "image" && a.previewUrl ? (
                <img src={a.previewUrl} alt={a.name} className="h-8 w-8 rounded object-cover" />
              ) : (
                <FileText className="h-4 w-4 text-muted-foreground" />
              )}
              <span className="max-w-[10rem] truncate" title={a.name}>{a.name}</span>
              {(a.status === "uploading" || a.status === "pending") && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />}
              {a.status === "failed" && <span className="text-destructive" title={a.error}>lỗi: {a.error || "tải lên thất bại"}</span>}
              {a.status === "ready" && <span className="text-emerald-600">✓</span>}
              <button onClick={() => onRemoveAttach(a.localId)} aria-label={`bỏ ${a.name}`} className="ml-1 text-muted-foreground hover:text-foreground">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
      <div className="mx-auto max-w-3xl flex items-end gap-2">
        <input
          ref={fileRef}
          type="file"
          multiple
          accept={ATTACH_ACCEPT}
          className="hidden"
          onChange={(e) => { if (e.target.files) onAttach(e.target.files); if (fileRef.current) fileRef.current.value = ""; }}
        />
        <Button
          variant="outline"
          size="icon"
          onClick={() => fileRef.current?.click()}
          aria-label="đính kèm tệp/ảnh vào tin nhắn"
          title="Đính kèm ảnh, .txt, .md, .docx, .pdf vào câu hỏi này"
        >
          <Paperclip className="h-4 w-4" />
        </Button>
        <Textarea
          ref={taRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder={dragOver ? "Thả tệp để đính kèm…" : "Hỏi tri thức, số liệu, hoặc đính kèm tệp… (Enter để gửi, Shift+Enter xuống dòng)"}
          className="min-h-[44px] resize-none overflow-y-auto"
          aria-label="ô nhập câu hỏi"
        />
        {sending ? (
          <Button variant="outline" size="icon" onClick={onStop} aria-label="dừng">
            <Square className="h-4 w-4" />
          </Button>
        ) : (
          <Button size="icon" onClick={submit} disabled={blockSend} aria-label="gửi">
            <Send className="h-4 w-4" />
          </Button>
        )}
      </div>
      {anyProcessing && <div className="mx-auto max-w-3xl mt-1 text-xs text-muted-foreground">Đang xử lý tệp đính kèm…</div>}
      {anyFailed && (
        <div className="mx-auto max-w-3xl mt-1 text-xs text-destructive">
          Có tệp đính kèm bị lỗi — gỡ bỏ (nút ✕) rồi gửi lại để câu trả lời không bị thiếu thông tin.
        </div>
      )}
    </div>
  );
}
