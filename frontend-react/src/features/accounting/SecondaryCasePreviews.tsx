import { useState } from "react";
import { api } from "@/api/client";
import { Badge, Button, Card } from "@/components/ui";

type Check = { check_id: string; status: "pass" | "fail" | "abstain"; reason_code: string };
type Close = { ready: boolean; blocker_ids: string[]; reason_codes: string[]; execution: string };
const tone = (value: string) => value === "pass" || value === "ready" ? "ok" : value === "fail" ? "warn" : "muted" as const;

export function SecondaryCasePreviews() {
  const [voucher, setVoucher] = useState<Check[] | null>(null);
  const [close, setClose] = useState<Close | null>(null);
  const [error, setError] = useState<string | null>(null);
  const runVoucher = async () => { try { setError(null); setVoucher(await api<Check[]>("/api/v2/accounting-cases/preview/voucher-review", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ invoice_total: "1100000", invoice_tax: "100000", invoice_net: "1000000", po_amount: "1100000", received: true, bravo_document_id: "synthetic-draft-voucher-001", duplicate_document_ids: [] }) })); } catch (e) { setError(e instanceof Error ? e.message : "Không chạy được Voucher preview."); } };
  const runClose = async () => { try { setError(null); setClose(await api<Close>("/api/v2/accounting-cases/preview/period-close-readiness", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prerequisites: [{ prerequisite_id: "bank-reconciliation", required: true, status: "complete", evidence_fresh: true }], reconciliations: [{ case_id: "case_12345678", status: "reviewed", material: true }] }) })); } catch (e) { setError(e instanceof Error ? e.message : "Không chạy được Period Close preview."); } };
  return <Card className="p-4"><h3 className="font-medium">Developer previews · Voucher & Period Close</h3><p className="mt-1 text-xs text-muted-foreground">Synthetic, read-only deterministic checks. Không posting voucher, close calculation, report hay period lock.</p><div className="mt-3 flex flex-wrap gap-2"><Button size="sm" variant="outline" onClick={() => void runVoucher()}>Chạy Voucher preview</Button><Button size="sm" variant="outline" onClick={() => void runClose()}>Chạy Period Close preview</Button></div>{error && <p className="mt-2 text-sm text-destructive">{error}</p>}{voucher && <div className="mt-3 space-y-1 text-sm">{voucher.map(item => <div className="flex justify-between" key={item.check_id}><span>{item.check_id} · {item.reason_code}</span><Badge tone={tone(item.status)}>{item.status}</Badge></div>)}</div>}{close && <div className="mt-3 text-sm"><Badge tone={tone(close.ready ? "ready" : "fail")}>{close.ready ? "ready" : "blocked"}</Badge><p className="mt-2">{close.reason_codes.join(", ") || "Không có blocker"}</p><p className="text-xs text-muted-foreground">{close.execution}</p></div>}</Card>;
}
