import { useRef, useState } from "react";
import { Paperclip, Send, Square } from "lucide-react";
import { Button, Textarea } from "@/components/ui";
import { cn } from "@/lib/utils";

interface Props {
  onSend: (q: string) => void;
  sending: boolean;
  onStop: () => void;
  onUpload?: (files: FileList | null) => void | Promise<void>;
  uploading?: boolean;
}

export function Composer({ onSend, sending, onStop, onUpload, uploading }: Props) {
  const [text, setText] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const submit = () => {
    const q = text.trim();
    if (!q || sending) return;
    onSend(q);
    setText("");
  };

  return (
    <div
      className={cn("border-t border-border bg-background p-3", dragOver && "ring-2 ring-primary ring-inset")}
      onDragOver={onUpload ? (e) => { e.preventDefault(); setDragOver(true); } : undefined}
      onDragLeave={onUpload ? () => setDragOver(false) : undefined}
      onDrop={onUpload ? (e) => { e.preventDefault(); setDragOver(false); onUpload(e.dataTransfer.files); } : undefined}
    >
      <div className="mx-auto max-w-3xl flex items-end gap-2">
        {onUpload && (
          <>
            <input
              ref={fileRef}
              type="file"
              multiple
              accept=".xml,.pdf,.docx,.xlsx,text/xml,application/pdf"
              className="hidden"
              onChange={(e) => { onUpload(e.target.files); if (fileRef.current) fileRef.current.value = ""; }}
            />
            <Button
              variant="outline"
              size="icon"
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              aria-label="đính kèm hoá đơn / tài liệu"
              title="Thả hoặc chọn hoá đơn XML / tài liệu (PDF, DOCX, XLSX)"
            >
              <Paperclip className="h-4 w-4" />
            </Button>
          </>
        )}
        <Textarea
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder={dragOver ? "Thả tệp để nạp…" : "Hỏi tri thức, số liệu, hoặc yêu cầu agent… (Enter để gửi)"}
          className="min-h-[44px] max-h-40"
          aria-label="ô nhập câu hỏi"
        />
        {sending ? (
          <Button variant="outline" size="icon" onClick={onStop} aria-label="dừng">
            <Square className="h-4 w-4" />
          </Button>
        ) : (
          <Button size="icon" onClick={submit} aria-label="gửi">
            <Send className="h-4 w-4" />
          </Button>
        )}
      </div>
      {uploading && <div className="mx-auto max-w-3xl mt-1 text-xs text-muted-foreground">Đang nạp tệp…</div>}
    </div>
  );
}
