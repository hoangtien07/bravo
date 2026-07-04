import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Download, FileSearch, Upload, X } from "lucide-react";
import { api, authHeaders } from "@/api/client";
import { Badge, Button, Card } from "@/components/ui";
import { DraftCard } from "@/features/chat/DraftCard";
import { cn, fmtMoney } from "@/lib/utils";
import type { Draft, JournalPayload } from "@/api/types";

const STATUSES = [
  { key: "", label: "Tất cả" },
  { key: "pending", label: "Chờ duyệt" },
  { key: "approved", label: "Đã duyệt" },
  { key: "rejected", label: "Từ chối" },
];
const STATUS_TONE: Record<string, "muted" | "ok" | "warn"> = {
  pending: "warn", approved: "ok", rejected: "muted",
};

export function MoneyEnginePage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [sel, setSel] = useState<Set<string>>(new Set());
  const [detail, setDetail] = useState<JournalPayload | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const nav = useNavigate();

  const load = () => {
    const qs = status ? `?status=${status}&kind=journal_entry` : `?kind=journal_entry`;
    api<Draft[]>(`/api/drafts${qs}`).then(setDrafts).catch(() => setDrafts([]));
  };
  useEffect(() => { load(); }, [status]);

  const upload = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true);
    let ok = 0, fail = 0;
    for (const f of Array.from(files)) {
      const fd = new FormData();
      fd.append("file", f);
      try {
        const r = await fetch("/api/invoices/draft", { method: "POST", headers: authHeaders(), body: fd });
        r.ok ? ok++ : fail++;
      } catch { fail++; }
    }
    setBusy(false);
    setMsg(`Đã nạp ${ok} hoá đơn${fail ? `, ${fail} lỗi` : ""}.`);
    setStatus("pending");
    load();
  };

  const approve = async (id: string) => {
    await api(`/api/drafts/${id}/approve`, { method: "POST" }).catch((e) => alert(e instanceof Error ? e.message : "Lỗi"));
    load();
  };
  const reject = async (id: string) => {
    const reason = prompt("Lý do từ chối?", "Cần sửa");
    if (reason === null) return;
    await api(`/api/drafts/${id}/reject`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason }),
    });
    load();
  };

  const toggle = (id: string) =>
    setSel((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const exportBatch = async () => {
    const ids = [...sel];
    if (!ids.length) { alert("Chọn ít nhất 1 bút toán để xuất lô."); return; }
    const r = await fetch("/api/drafts/export", {
      method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ draft_ids: ids }),
    });
    if (!r.ok) { alert("Lỗi xuất lô"); return; }
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement("a");
    a.href = url; a.download = "buttoan_lo.csv"; document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  };

  const inv = (detail?.invoice || {}) as Record<string, string>;

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2">
        <Button variant="ghost" size="icon" onClick={() => nav("/")} aria-label="quay lại"><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="font-semibold tracking-tight">Hoá đơn → bút toán nháp (TT99)</h1>
      </header>

      <div className="mx-auto max-w-3xl p-4 space-y-4">
        {/* Upload */}
        <Card className="p-6 text-center border-dashed">
          <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
          <p className="text-sm text-muted-foreground my-2">
            Thả/chọn hoá đơn điện tử XML — hệ sinh bút toán nháp cân Nợ=Có, map TK TT99, cờ TSCĐ/VAT theo luật.
          </p>
          <label className="inline-block">
            <input type="file" accept=".xml,text/xml" multiple className="hidden" onChange={(e) => upload(e.target.files)} />
            <span className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm cursor-pointer hover:bg-primary/90">
              {busy ? "Đang xử lý…" : "Chọn hoá đơn XML"}
            </span>
          </label>
          {msg && <p className="text-xs text-muted-foreground mt-2">{msg}</p>}
        </Card>

        {/* Bộ lọc trạng thái + export lô */}
        <div className="flex items-center gap-2 flex-wrap">
          {STATUSES.map((s) => (
            <button key={s.key} onClick={() => { setStatus(s.key); setSel(new Set()); }}
                    className={cn("rounded-md px-3 py-1 text-sm border border-border",
                      status === s.key ? "bg-primary text-primary-foreground" : "hover:bg-muted")}>
              {s.label}
            </button>
          ))}
          <Button size="sm" variant="outline" className="ml-auto" onClick={exportBatch} disabled={!sel.size}>
            <Download className="h-4 w-4" /> Xuất lô CSV ({sel.size})
          </Button>
        </div>

        {/* Danh sách draft */}
        {drafts.map((d) => (
          <div key={d.id} className="flex gap-2">
            <input type="checkbox" checked={sel.has(d.id)} onChange={() => toggle(d.id)}
                   className="mt-4 accent-primary" aria-label="chọn để xuất lô" />
            <div className="flex-1 min-w-0">
              <DraftCard payload={d.payload as JournalPayload} draftId={d.id}
                         onApprove={approve} onReject={reject} readOnly={d.status !== "pending"} />
              <div className="flex items-center gap-2 mt-1 ml-1">
                <Badge tone={STATUS_TONE[d.status] || "muted"}>{d.status}</Badge>
                <button onClick={() => setDetail(d.payload as JournalPayload)}
                        className="text-xs text-primary hover:underline inline-flex items-center gap-1">
                  <FileSearch className="h-3 w-3" /> Chi tiết hoá đơn gốc
                </button>
              </div>
            </div>
          </div>
        ))}
        {!drafts.length && <p className="text-sm text-muted-foreground">Chưa có bút toán nháp nào.</p>}
      </div>

      {/* Modal chi tiết hoá đơn gốc */}
      {detail && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setDetail(null)}>
          <Card className="max-w-2xl w-full max-h-[80vh] overflow-auto p-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-1">
              <h3 className="font-semibold">Chi tiết hoá đơn gốc</h3>
              <button onClick={() => setDetail(null)} aria-label="đóng"><X className="h-4 w-4" /></button>
            </div>
            <div className="text-xs text-muted-foreground mb-3">
              HĐ {inv.ky_hieu}-{inv.so_hoa_don} · Bên bán {inv.ten_ban} (MST {inv.mst_ban}) · {inv.ngay_lap}
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="py-1">Tên hàng</th><th>ĐVT</th><th className="text-right">SL</th>
                  <th className="text-right">Đơn giá</th><th className="text-right">Thành tiền</th>
                  <th className="text-right">Thuế</th><th className="text-right">Tiền thuế</th>
                </tr>
              </thead>
              <tbody>
                {(detail.invoice_lines || []).map((l, i) => (
                  <tr key={i} className="border-b border-border">
                    <td className="py-1">{l.ten_hang}</td><td>{l.dvt}</td>
                    <td className="text-right tabular">{fmtMoney(l.so_luong)}</td>
                    <td className="text-right tabular">{fmtMoney(l.don_gia)}</td>
                    <td className="text-right tabular">{fmtMoney(l.thanh_tien)}</td>
                    <td className="text-right">{l.thue_suat}%</td>
                    <td className="text-right tabular">{fmtMoney(l.tien_thue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!detail.invoice_lines?.length && (
              <p className="text-sm text-muted-foreground">Hoá đơn này chưa lưu chi tiết dòng hàng (nạp trước bản cập nhật).</p>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
