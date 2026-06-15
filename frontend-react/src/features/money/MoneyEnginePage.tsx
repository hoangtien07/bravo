import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Upload } from "lucide-react";
import { api, authHeaders } from "@/api/client";
import { Button, Card } from "@/components/ui";
import { DraftCard } from "@/features/chat/DraftCard";
import type { Draft } from "@/api/types";

// Panel money-engine (hybrid): upload nhiều hoá đơn XML -> bút toán nháp -> duyệt.
export function MoneyEnginePage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const load = () => api<Draft[]>("/api/drafts").then(setDrafts).catch(() => {});
  useEffect(() => { load(); }, []);

  const upload = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true);
    for (const f of Array.from(files)) {
      const fd = new FormData();
      fd.append("file", f);
      try {
        await fetch("/api/invoices/draft", { method: "POST", headers: authHeaders(), body: fd });
      } catch {
        /* ignore single failure */
      }
    }
    setBusy(false);
    load();
  };

  const approve = async (id: string) => { await api(`/api/drafts/${id}/approve`, { method: "POST" }).catch((e) => alert(e.message)); load(); };
  const reject = async (id: string) => {
    const reason = prompt("Lý do từ chối?", "Cần sửa");
    if (reason === null) return;
    await api(`/api/drafts/${id}/reject`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason }) });
    load();
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2">
        <Button variant="ghost" size="icon" onClick={() => nav("/")} aria-label="quay lại"><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="font-semibold tracking-tight">Hoá đơn → bút toán nháp (TT99)</h1>
      </header>
      <div className="mx-auto max-w-3xl p-4 space-y-4">
        <Card className="p-6 text-center border-dashed">
          <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
          <p className="text-sm text-muted-foreground my-2">Thả hoá đơn điện tử XML — hệ sinh bút toán nháp cân Nợ=Có, map TK TT99, trích dẫn tới dòng.</p>
          <label className="inline-block">
            <input type="file" accept=".xml,text/xml" multiple className="hidden" onChange={(e) => upload(e.target.files)} />
            <span className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm cursor-pointer hover:bg-primary/90">
              {busy ? "Đang xử lý…" : "Chọn hoá đơn XML"}
            </span>
          </label>
        </Card>
        <div className="text-sm font-medium text-muted-foreground">Nháp chờ duyệt</div>
        {drafts.filter((d) => d.kind === "journal_entry").map((d) => (
          <DraftCard key={d.id} payload={d.payload as any} draftId={d.id} onApprove={approve} onReject={reject} />
        ))}
        {!drafts.length && <p className="text-sm text-muted-foreground">Chưa có nháp nào.</p>}
      </div>
    </div>
  );
}
