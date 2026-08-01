import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, ClipboardList, MessageCircleQuestion, RefreshCw, Settings2, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { Badge, Button, Card, Input, Spinner } from "@/components/ui";
import type { AccountingCaseView, AccountingConversationReply } from "@/api/types";
import { SecondaryCasePreviews } from "./SecondaryCasePreviews";

const tone = (state: string) => state === "REVIEWED" || state === "EXPORTED" ? "ok" : state === "NEEDS_REVIEW" ? "warn" : "muted" as const;

export function AccountingWorkPage() {
  const [cases, setCases] = useState<AccountingCaseView[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<AccountingCaseView | null>(null);
  const [question, setQuestion] = useState("");
  const [reply, setReply] = useState<AccountingConversationReply | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async (caseId = selected) => {
    setLoading(true); setError(null);
    try {
      const rows = await api<AccountingCaseView[]>("/api/v2/accounting-cases");
      setCases(rows);
      const next = caseId || rows[0]?.case_id || null;
      setSelected(next);
      setDetail(next ? await api<AccountingCaseView>(`/api/v2/accounting-cases/${next}`) : null);
    } catch (e) { setError(e instanceof Error ? e.message : "Không tải được Accounting Work."); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);
  const current = useMemo(() => cases.find((item) => item.case_id === selected), [cases, selected]);

  const choose = async (id: string) => { setSelected(id); setReply(null); try { setDetail(await api(`/api/v2/accounting-cases/${id}`)); } catch { await load(id); } };
  const ask = async () => {
    if (!selected || !question.trim()) return;
    setReply(null);
    try { setReply(await api<AccountingConversationReply>(`/api/v2/accounting-cases/${selected}/conversation`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) })); }
    catch (e) { setError(e instanceof Error ? e.message : "Không thể diễn giải finding."); }
  };

  return <div className="flex-1 min-h-0 bg-background flex flex-col">
    <header className="px-6 py-4 border-b bg-card flex items-center justify-between">
      <div><p className="text-xs uppercase tracking-[0.18em] text-primary font-semibold">Accounting operations</p><h1 className="text-xl font-semibold">Công việc AI</h1></div>
      <div className="flex gap-2"><Link to="/governance-integration"><Button variant="outline" size="sm"><Settings2 className="h-4 w-4" /> Governance mock</Button></Link><Button variant="outline" size="sm" onClick={() => void load()}><RefreshCw className="h-4 w-4" /> Làm mới</Button></div>
    </header>
    <div className="p-4 bg-warning-bg/40 text-sm border-b"><ShieldCheck className="h-4 w-4 inline mr-2 text-warning" />Dữ liệu synthetic. Mọi export chỉ tạo artifact review; BRAVO không thực thi thao tác nào.</div>
    <div className="flex-1 min-h-0 grid grid-cols-[18rem_minmax(0,1fr)]">
      <aside className="border-r overflow-auto p-3 space-y-2">{loading && <Spinner />}{error && <p className="text-sm text-destructive">{error}</p>}{!loading && !cases.length && <p className="text-sm text-muted-foreground">Chưa có case được cấp quyền.</p>}
        {cases.map((item) => <button key={item.case_id} onClick={() => void choose(item.case_id)} className={`w-full text-left p-3 rounded-lg border ${item.case_id === selected ? "border-primary bg-primary/5" : "hover:bg-muted"}`}><div className="flex justify-between gap-2"><span className="font-medium text-sm">Bank reconciliation</span><Badge tone={tone(item.state)}>{item.state}</Badge></div><p className="mt-2 text-xs text-muted-foreground truncate">{item.case_id}</p></button>)}</aside>
      <main className="overflow-auto p-5 max-w-5xl w-full">{detail ? <div className="space-y-4">
        <div className="flex items-start justify-between"><div><h2 className="text-lg font-semibold">Hồ sơ case</h2><p className="text-sm text-muted-foreground">Revision {detail.revision} · {detail.case_id}</p></div><Badge tone={tone(detail.state)}>{detail.state}</Badge></div>
        <Card className="p-4"><h3 className="font-medium flex gap-2 items-center"><ClipboardList className="h-4 w-4" /> Evidence hiện tại</h3><div className="mt-3 grid sm:grid-cols-2 gap-2">{detail.evidence.map((item) => <div key={item.snapshot_id} className="rounded border p-2 text-sm"><b>{item.source_type}</b><br /><span className="text-muted-foreground">{item.source_version} · {item.complete ? "complete" : "missing"}</span></div>)}</div></Card>
        <Card className="p-4"><h3 className="font-medium flex gap-2 items-center"><AlertTriangle className="h-4 w-4" /> Findings</h3><div className="mt-3 space-y-2">{detail.findings.length ? detail.findings.map((item) => <div key={item.finding_id} className="border rounded p-3 text-sm flex justify-between"><span><b>{item.finding_id}</b> · {item.finding_type}<br /><span className="text-muted-foreground">Rule: {item.check_result_ids.join(", ")}</span></span><Badge tone={item.severity === "high" ? "warn" : "muted"}>{item.severity}</Badge></div>) : <p className="text-sm text-muted-foreground">Không có exception cần review.</p>}</div></Card>
        <Card className="p-4"><h3 className="font-medium flex gap-2 items-center"><MessageCircleQuestion className="h-4 w-4" /> Hỏi về finding</h3><p className="text-xs text-muted-foreground mt-1">Chỉ diễn giải evidence/rule đã kiểm tra; không đổi kết quả hay trạng thái case.</p><div className="mt-3 flex gap-2"><Input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ví dụ: Giải thích finding-001" /><Button onClick={() => void ask()}>Hỏi</Button></div>{reply && <div className="mt-3 rounded border bg-muted/40 p-3 text-sm"><Badge tone={reply.kind === "abstention" ? "warn" : "primary"}>{reply.kind}</Badge><p className="mt-2">{reply.text}</p><p className="mt-2 text-xs text-muted-foreground">Evidence: {reply.evidence_snapshot_ids.join(", ") || "—"} · Rules: {reply.rule_ids.join(", ") || "—"}</p></div>}</Card>
        <SecondaryCasePreviews />
      </div> : <p className="text-muted-foreground">Chọn một case để xem.</p>}</main>
    </div>
  </div>;
}
