import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Check, Download, Inbox, X } from "lucide-react";
import { api, authHeaders, downloadFile } from "@/api/client";
import { Badge, Button, Card } from "@/components/ui";
import { DraftCard } from "@/features/chat/DraftCard";
import { cn, fmtMoney } from "@/lib/utils";
import type { Draft, JournalPayload } from "@/api/types";

const STATUSES = [
  { key: "pending", label: "Chờ duyệt" },
  { key: "approved", label: "Đã duyệt" },
  { key: "rejected", label: "Từ chối" },
  { key: "", label: "Tất cả" },
];
const STATUS_TONE: Record<string, "muted" | "ok" | "warn"> = {
  pending: "warn", approved: "ok", rejected: "muted",
};

// Hàng đợi duyệt TẬP TRUNG (W1.6) — mọi loại nháp, cho kế toán trưởng duyệt lô + xuất file
// nhập tay ERP (ADR-0016). Backend: GET/POST /api/drafts (RLS-scoped, maker-checker).
export function DraftsQueuePage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [status, setStatus] = useState("pending");
  const [sel, setSel] = useState<Set<string>>(new Set());
  const [msg, setMsg] = useState<string | null>(null);
  const nav = useNavigate();

  const load = () => {
    const qs = status ? `?status=${status}` : "";
    api<Draft[]>(`/api/drafts${qs}`).then(setDrafts).catch((e) =>
      setMsg(e instanceof Error ? e.message : "Không tải được (cần quyền draft:approve)"));
  };
  useEffect(() => { load(); setSel(new Set()); }, [status]);

  const approve = async (id: string) => {
    await api(`/api/drafts/${id}/approve`, { method: "POST" })
      .catch((e) => alert(e instanceof Error ? e.message : "Lỗi duyệt"));
    load();
  };
  const reject = async (id: string) => {
    const reason = prompt("Lý do từ chối?", "Cần sửa");
    if (reason === null) return;
    await api(`/api/drafts/${id}/reject`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    }).catch((e) => alert(e instanceof Error ? e.message : "Lỗi"));
    load();
  };

  const toggle = (id: string) =>
    setSel((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const approvedJournalIds = drafts
    .filter((d) => d.kind === "journal_entry" && d.status === "approved")
    .map((d) => d.id);
  const exportBatch = async () => {
    const ids = [...sel].filter((id) => approvedJournalIds.includes(id));
    if (!ids.length) { alert("Chọn ít nhất 1 bút toán (journal_entry) để xuất lô."); return; }
    const r = await fetch("/api/drafts/export", {
      method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ draft_ids: ids }),
    });
    if (!r.ok) { alert("Lỗi xuất lô"); return; }
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement("a");
    a.href = url; a.download = "buttoan_lo.csv";
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  };

  // Tổng Nợ/Có của các bút toán đang chọn (cho kế toán trưởng soát lô).
  const selTotals = drafts
    .filter((d) => sel.has(d.id) && d.kind === "journal_entry")
    .reduce((acc, d) => {
      const p = d.payload as JournalPayload;
      return { debit: acc.debit + Number(p.total_debit || 0), credit: acc.credit + Number(p.total_credit || 0) };
    }, { debit: 0, credit: 0 });

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2">
        <Button variant="ghost" size="icon" onClick={() => nav("/")} aria-label="quay lại"><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="font-semibold tracking-tight flex items-center gap-2">
          <Inbox className="h-4 w-4" /> Hàng đợi duyệt nháp
        </h1>
      </header>

      <div className="mx-auto max-w-3xl p-4 space-y-3">
        <p className="text-xs text-muted-foreground">
          Nháp do AI/hoá đơn đề xuất, chờ người duyệt (maker-checker: người duyệt ≠ người tạo).
          Duyệt xong <b>xuất Excel/CSV</b> để nhập tay vào ERP — con người là cổng ghi cuối (ADR-0016).
        </p>

        <div className="flex items-center gap-2 flex-wrap">
          {STATUSES.map((s) => (
            <button key={s.key} onClick={() => setStatus(s.key)}
                    className={cn("rounded-md px-3 py-1 text-sm border border-border",
                      status === s.key ? "bg-primary text-primary-foreground" : "hover:bg-muted")}>
              {s.label}
            </button>
          ))}
          <Button size="sm" variant="outline" className="ml-auto" onClick={exportBatch} disabled={!sel.size}>
            <Download className="h-4 w-4" /> Xuất lô CSV ({sel.size})
          </Button>
        </div>

        {sel.size > 0 && (
          <div className="text-xs text-muted-foreground rounded-md bg-muted/40 px-3 py-2">
            Đang chọn {sel.size} nháp · Σ Nợ <b className="tabular">{fmtMoney(String(selTotals.debit))}</b>
            {" "}· Σ Có <b className="tabular">{fmtMoney(String(selTotals.credit))}</b>
          </div>
        )}
        {msg && <div className="text-xs text-destructive">{msg}</div>}

        {drafts.map((d) => (
          <div key={d.id} className="flex gap-2">
            <input type="checkbox" checked={sel.has(d.id)} onChange={() => toggle(d.id)}
                   disabled={d.kind !== "journal_entry" || d.status !== "approved"}
                   className="mt-4 accent-primary" aria-label="chọn để xuất lô" />
            <div className="flex-1 min-w-0">
              {d.kind === "journal_entry" ? (
                <DraftCard payload={d.payload as JournalPayload} draftId={d.id} status={d.status}
                           onApprove={approve} onReject={reject} readOnly={d.status !== "pending"} />
              ) : (
                <Card className="p-3">
                  <div className="text-sm font-medium">{d.kind}</div>
                  <pre className="text-xs text-muted-foreground overflow-auto mt-1 max-h-40">
                    {JSON.stringify(d.payload, null, 2)}
                  </pre>
                  {d.status === "pending" && (
                    <div className="flex gap-2 mt-2">
                      <Button size="sm" onClick={() => approve(d.id)}><Check className="h-3.5 w-3.5" /> Duyệt</Button>
                      <Button size="sm" variant="outline" onClick={() => reject(d.id)}><X className="h-3.5 w-3.5" /> Từ chối</Button>
                    </div>
                  )}
                </Card>
              )}
              <div className="flex items-center gap-2 mt-1 ml-1">
                <Badge tone={STATUS_TONE[d.status] || "muted"}>{d.status}</Badge>
                {d.kind === "journal_entry" && d.status === "approved" && (
                  <>
                    <button onClick={() => downloadFile(`/api/drafts/${d.id}/export?fmt=csv`, `buttoan_${d.id.slice(0, 8)}.csv`)}
                            className="text-xs text-primary hover:underline">CSV</button>
                    <button onClick={() => downloadFile(`/api/drafts/${d.id}/export?fmt=xlsx`, `buttoan_${d.id.slice(0, 8)}.xlsx`)}
                            className="text-xs text-primary hover:underline">XLSX</button>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        {!drafts.length && !msg && <p className="text-sm text-muted-foreground">Không có nháp nào ở trạng thái này.</p>}
      </div>
    </div>
  );
}
