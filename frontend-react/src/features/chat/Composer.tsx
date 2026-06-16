import { useState } from "react";
import { Send, Square } from "lucide-react";
import { Button, Textarea } from "@/components/ui";

interface Props {
  onSend: (q: string) => void;
  sending: boolean;
  onStop: () => void;
}

export function Composer({ onSend, sending, onStop }: Props) {
  const [text, setText] = useState("");
  const submit = () => {
    const q = text.trim();
    if (!q || sending) return;
    onSend(q);
    setText("");
  };
  return (
    <div className="border-t border-border bg-background p-3">
      <div className="mx-auto max-w-3xl flex items-end gap-2">
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
          placeholder="Hỏi tri thức, số liệu, hoặc yêu cầu agent… (Enter để gửi)"
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
    </div>
  );
}
