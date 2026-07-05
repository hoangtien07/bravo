import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Check, FileCheck2, Info, ScanLine, X } from "lucide-react";
import { api } from "@/api/client";
import { Badge, Button, Card } from "@/components/ui";
import { DemoBanner } from "@/components/DemoBanner";
import { fmtMoney } from "@/lib/utils";
import type { Draft } from "@/api/types";

interface TaxFlag {
  ky: string; loai: string; mo_ta: string;
  so_hd_thuc: string; so_khai: string; chenh_lech: string;
  muc_do: number; bang_chung: string[];
}

export function TaxPage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const nav = useNavigate();

  const load = () =>
    api<Draft[]>("/api/drafts?kind=tax_adjustment&status=pending").then(setDrafts).catch(() => setDrafts([]));
  useEffect(() => { load(); }, []);

  const reconcile = async () => {
    setBusy(true);
    try {
      const r = await api<{ created: number; total_flags: number }>("/api/agents/tax/reconcile", { method: "POST" });
      setMsg(`Đối chiếu: ${r.total_flags} sai lệch (${r.created} kiến nghị mới).`);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Lỗi đối chiếu");
    }
    setBusy(false);
    load();
  };

  const approve = async (id: string) => {
    await api(`/api/drafts/${id}/approve`, { method: "POST" }).catch((e) => alert(e instanceof Error ? e.message : "Lỗi"));
    load();
  };
  const dismiss = async (id: string) => {
    await api(`/api/drafts/${id}/reject`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason: "Bỏ qua" }),
    });
    load();
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2">
        <Button variant="ghost" size="icon" onClick={() => nav("/")} aria-label="quay lại"><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="font-semibold tracking-tight flex items-center gap-2">
          <FileCheck2 className="h-4 w-4 text-primary" /> Trợ lý thuế
        </h1>
        <Button size="sm" className="ml-auto" onClick={reconcile} disabled={busy}>
          <ScanLine className="h-4 w-4" /> {busy ? "Đang đối chiếu…" : "Đối chiếu hoá đơn ↔ tờ khai"}
        </Button>
      </header>

      <div className="mx-auto max-w-3xl p-4 space-y-3">
        <DemoBanner note="Lớp 2 (đối chiếu hoá đơn ↔ tờ khai) chạy trên số mock; phần tra cứu luật (RAG) hoạt động trên tài liệu thật đã nạp." />
        <div className="flex items-start gap-2 rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
          <Info className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <b>Tra cứu luật thuế (RAG):</b> nạp tài liệu luật (TT/NĐ thuế) qua trang "Hoá đơn → bút toán"
            hoặc thư mục nguồn, rồi hỏi ở khung <button className="text-primary underline" onClick={() => nav("/")}>Chat</button> — câu trả lời có trích dẫn.
            <br /><b>Đối chiếu (Lớp 2):</b> engine so tổng thuế từ hoá đơn với tờ khai → kiến nghị chờ duyệt.
          </div>
        </div>
        {msg && <div className="text-xs text-muted-foreground">{msg}</div>}

        {drafts.map((d) => {
          const f = d.payload as unknown as TaxFlag;
          return (
            <Card key={d.id} className="p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-medium">{f.mo_ta}</div>
                  <div className="text-xs text-muted-foreground">
                    Kỳ {f.ky}
                    {f.chenh_lech !== "0" && <> · chênh lệch <b>{fmtMoney(f.chenh_lech)}đ</b></>}
                  </div>
                </div>
                <Badge tone="warn">Mức {f.muc_do >= 2 ? "cao" : "thấp"}</Badge>
              </div>
              <ul className="mt-2 space-y-0.5 text-xs">
                {(f.bang_chung || []).map((b, i) => (
                  <li key={i} className="flex items-start gap-1 text-muted-foreground"><span className="text-warning">•</span> {b}</li>
                ))}
              </ul>
              <div className="flex gap-2 mt-3">
                <Button size="sm" onClick={() => approve(d.id)}><Check className="h-4 w-4" /> Lập kiến nghị</Button>
                <Button size="sm" variant="ghost" onClick={() => dismiss(d.id)}><X className="h-4 w-4" /> Bỏ qua</Button>
              </div>
            </Card>
          );
        })}
        {!drafts.length && (
          <p className="text-sm text-muted-foreground">Chưa có kiến nghị. Bấm "Đối chiếu hoá đơn ↔ tờ khai".</p>
        )}
      </div>
    </div>
  );
}
