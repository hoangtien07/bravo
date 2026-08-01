import { useState } from "react";
import { Calculator, ClipboardCheck, Play } from "lucide-react";
import { api } from "@/api/client";
import { Badge, Button, Card, Input } from "@/components/ui";

type Check = { check_id: string; status: "pass" | "fail" | "abstain"; reason_code: string };
type Close = { ready: boolean; blocker_ids: string[]; reason_codes: string[]; execution: string };
type VoucherForm = { total: string; tax: string; net: string; po: string; received: "yes" | "no" | "missing"; draftId: string; duplicate: boolean };
type CloseForm = { prerequisite: "complete" | "pending"; fresh: boolean; reconciliation: "reviewed" | "unresolved" | "missing"; material: boolean };

const tone = (value: string) => value === "pass" || value === "ready" ? "ok" : value === "fail" || value === "blocked" ? "warn" : "muted" as const;
const inputLabel = "text-xs font-medium text-muted-foreground";

export function SecondaryCasePreviews() {
  const [voucherForm, setVoucherForm] = useState<VoucherForm>({ total: "1100000", tax: "100000", net: "1000000", po: "1100000", received: "yes", draftId: "synthetic-draft-voucher-001", duplicate: false });
  const [closeForm, setCloseForm] = useState<CloseForm>({ prerequisite: "complete", fresh: true, reconciliation: "reviewed", material: true });
  const [voucher, setVoucher] = useState<Check[] | null>(null);
  const [close, setClose] = useState<Close | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"voucher" | "close" | null>(null);

  const runVoucher = async () => {
    setBusy("voucher"); setError(null);
    try {
      setVoucher(await api<Check[]>("/api/v2/accounting-cases/preview/voucher-review", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ invoice_total: voucherForm.total, invoice_tax: voucherForm.tax, invoice_net: voucherForm.net, po_amount: voucherForm.po || null, received: voucherForm.received === "missing" ? null : voucherForm.received === "yes", bravo_document_id: voucherForm.draftId || null, duplicate_document_ids: voucherForm.duplicate ? ["synthetic-duplicate-001"] : [] }) }));
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Không thể chạy Voucher preview."); }
    finally { setBusy(null); }
  };
  const runClose = async () => {
    setBusy("close"); setError(null);
    try {
      setClose(await api<Close>("/api/v2/accounting-cases/preview/period-close-readiness", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prerequisites: [{ prerequisite_id: "bank-reconciliation", required: true, status: closeForm.prerequisite, evidence_fresh: closeForm.fresh }], reconciliations: [{ case_id: "case_12345678", status: closeForm.reconciliation, material: closeForm.material }] }) }));
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Không thể chạy Period Close preview."); }
    finally { setBusy(null); }
  };
  const updateVoucher = <K extends keyof VoucherForm>(key: K, value: VoucherForm[K]) => setVoucherForm((current) => ({ ...current, [key]: value }));
  const updateClose = <K extends keyof CloseForm>(key: K, value: CloseForm[K]) => setCloseForm((current) => ({ ...current, [key]: value }));

  return <Card className="p-4">
    <div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-[0.16em] text-primary font-semibold">Developer workbench</p><h3 className="mt-1 font-medium">Voucher & Period Close checks</h3><p className="mt-1 text-xs text-muted-foreground">Nhập fixture synthetic để kiểm tra state pass, fail và abstain. Không posting voucher, tính close, tạo report hay lock kỳ.</p></div><Badge tone="primary">read-only</Badge></div>
    <div className="mt-4 grid gap-4 xl:grid-cols-2">
      <section className="rounded-lg border p-3"><div className="flex items-center gap-2"><Calculator className="h-4 w-4 text-primary" /><h4 className="font-medium text-sm">Voucher Evidence Review</h4></div><div className="mt-3 grid grid-cols-3 gap-2"><label className={inputLabel}>Tổng invoice<Input aria-label="Voucher total" value={voucherForm.total} onChange={(event) => updateVoucher("total", event.target.value)} /></label><label className={inputLabel}>Thuế<Input aria-label="Voucher tax" value={voucherForm.tax} onChange={(event) => updateVoucher("tax", event.target.value)} /></label><label className={inputLabel}>Net<Input aria-label="Voucher net" value={voucherForm.net} onChange={(event) => updateVoucher("net", event.target.value)} /></label></div><div className="mt-2 grid sm:grid-cols-2 gap-2"><label className={inputLabel}>PO amount (để trống = missing)<Input aria-label="Voucher PO amount" value={voucherForm.po} onChange={(event) => updateVoucher("po", event.target.value)} /></label><label className={inputLabel}>BRAVO draft ID (để trống = missing)<Input aria-label="Voucher draft id" value={voucherForm.draftId} onChange={(event) => updateVoucher("draftId", event.target.value)} /></label></div><div className="mt-2 flex flex-wrap gap-3 text-xs"><label>Receipt <select aria-label="Voucher receipt" value={voucherForm.received} onChange={(event) => updateVoucher("received", event.target.value as VoucherForm["received"])} className="ml-1 rounded border bg-card px-2 py-1"><option value="yes">received</option><option value="no">not received</option><option value="missing">missing</option></select></label><label className="flex gap-1 items-center"><input aria-label="Voucher duplicate" type="checkbox" checked={voucherForm.duplicate} onChange={(event) => updateVoucher("duplicate", event.target.checked)} /> Duplicate candidate</label></div><Button className="mt-3" size="sm" variant="outline" disabled={busy !== null} onClick={() => void runVoucher()}>{busy === "voucher" ? "Đang kiểm tra…" : <><Play className="h-4 w-4" /> Chạy Voucher checks</>}</Button>{voucher && <CheckList checks={voucher} />}</section>
      <section className="rounded-lg border p-3"><div className="flex items-center gap-2"><ClipboardCheck className="h-4 w-4 text-primary" /><h4 className="font-medium text-sm">Period Close Readiness</h4></div><div className="mt-3 grid sm:grid-cols-2 gap-2 text-xs"><label className={inputLabel}>Bank reconciliation<select aria-label="Close prerequisite" value={closeForm.prerequisite} onChange={(event) => updateClose("prerequisite", event.target.value as CloseForm["prerequisite"])} className="mt-1 h-10 w-full rounded border bg-card px-2"><option value="complete">complete</option><option value="pending">pending</option></select></label><label className={inputLabel}>Reconciliation reference<select aria-label="Close reconciliation" value={closeForm.reconciliation} onChange={(event) => updateClose("reconciliation", event.target.value as CloseForm["reconciliation"])} className="mt-1 h-10 w-full rounded border bg-card px-2"><option value="reviewed">reviewed</option><option value="unresolved">unresolved</option><option value="missing">missing</option></select></label></div><div className="mt-3 flex flex-wrap gap-3 text-xs"><label className="flex gap-1 items-center"><input aria-label="Close fresh evidence" type="checkbox" checked={closeForm.fresh} onChange={(event) => updateClose("fresh", event.target.checked)} /> Evidence fresh</label><label className="flex gap-1 items-center"><input aria-label="Close material reconciliation" type="checkbox" checked={closeForm.material} onChange={(event) => updateClose("material", event.target.checked)} /> Material reconciliation</label></div><Button className="mt-3" size="sm" variant="outline" disabled={busy !== null} onClick={() => void runClose()}>{busy === "close" ? "Đang kiểm tra…" : <><Play className="h-4 w-4" /> Chạy readiness checks</>}</Button>{close && <div className="mt-3 rounded border bg-muted/30 p-3 text-sm"><Badge tone={tone(close.ready ? "ready" : "blocked")}>{close.ready ? "ready" : "blocked"}</Badge><p className="mt-2">{close.reason_codes.join(", ") || "Không có blocker"}</p>{close.blocker_ids.length > 0 && <p className="mt-1 text-xs text-muted-foreground">Blockers: {close.blocker_ids.join(", ")}</p>}<p className="mt-2 text-xs text-muted-foreground">{close.execution}</p></div>}</section>
    </div>
    {error && <p role="alert" className="mt-3 rounded border border-destructive/40 bg-destructive/5 p-2 text-sm text-destructive">{error}</p>}
  </Card>;
}

function CheckList({ checks }: { checks: Check[] }) {
  return <div className="mt-3 space-y-1 text-sm">{checks.map((item) => <div className="flex justify-between gap-2" key={item.check_id}><span>{item.check_id} · {item.reason_code}</span><Badge tone={tone(item.status)}>{item.status}</Badge></div>)}</div>;
}
