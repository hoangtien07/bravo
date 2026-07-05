import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, ArrowLeft, Check, ScanLine, X } from "lucide-react";
import { api } from "@/api/client";
import { Badge, Button, Card } from "@/components/ui";
import { DemoBanner } from "@/components/DemoBanner";
import { fmtMoney } from "@/lib/utils";
import type { Draft } from "@/api/types";

interface Flag {
  loai: string; chung_tu: string; so_tien: string; mo_ta: string;
  muc_do: number; bang_chung: string[];
}
const SEVERITY: Record<number, { label: string; tone: "warn" | "ok" | "muted" }> = {
  3: { label: "Cao", tone: "warn" },
  2: { label: "Trung bình", tone: "warn" },
  1: { label: "Thấp", tone: "muted" },
};

export function AnomalyPage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const nav = useNavigate();

  const load = () =>
    api<Draft[]>("/api/drafts?kind=anomaly_flag&status=pending").then(setDrafts).catch(() => setDrafts([]));
  useEffect(() => { load(); }, []);

  const scan = async () => {
    setBusy(true);
    try {
      const r = await api<{ created: number; total_flags: number }>("/api/agents/anomaly/scan", { method: "POST" });
      setMsg(`Đã quét: ${r.total_flags} cờ bất thường (${r.created} cờ mới).`);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Lỗi quét");
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
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason: "Bỏ qua (không bất thường)" }),
    });
    load();
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2">
        <Button variant="ghost" size="icon" onClick={() => nav("/")} aria-label="quay lại"><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="font-semibold tracking-tight flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-warning" /> Soi bất thường
        </h1>
        <Button size="sm" className="ml-auto" onClick={scan} disabled={busy}>
          <ScanLine className="h-4 w-4" /> {busy ? "Đang quét…" : "Quét bất thường"}
        </Button>
      </header>

      <div className="mx-auto max-w-3xl p-4 space-y-3">
        <DemoBanner />
        <p className="text-xs text-muted-foreground">
          Engine tất định soi bút toán/hoá đơn bất thường (trùng · số tròn lớn · ngoài giờ) →
          tạo <b>cờ đỏ chờ kế toán xác nhận</b>. AI chỉ nghi ngờ + dẫn bằng chứng, KHÔNG tự kết luận gian lận.
        </p>
        {msg && <div className="text-xs text-muted-foreground">{msg}</div>}

        {drafts.map((d) => {
          const f = d.payload as unknown as Flag;
          const sev = SEVERITY[f.muc_do] || SEVERITY[1];
          return (
            <Card key={d.id} className="p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-medium">{f.mo_ta || f.loai}</div>
                  <div className="text-xs text-muted-foreground">Chứng từ {f.chung_tu} · {fmtMoney(f.so_tien)}đ</div>
                </div>
                <Badge tone={sev.tone}>Mức {sev.label}</Badge>
              </div>
              <ul className="mt-2 space-y-0.5 text-xs">
                {(f.bang_chung || []).map((b, i) => (
                  <li key={i} className="flex items-start gap-1 text-muted-foreground">
                    <span className="text-warning">⚠</span> {b}
                  </li>
                ))}
              </ul>
              <div className="flex gap-2 mt-3">
                <Button size="sm" onClick={() => approve(d.id)}><Check className="h-4 w-4" /> Xác nhận điều tra</Button>
                <Button size="sm" variant="ghost" onClick={() => dismiss(d.id)}><X className="h-4 w-4" /> Bỏ qua</Button>
              </div>
            </Card>
          );
        })}
        {!drafts.length && (
          <p className="text-sm text-muted-foreground">Chưa có cờ bất thường. Bấm "Quét bất thường" để chạy.</p>
        )}
      </div>
    </div>
  );
}
