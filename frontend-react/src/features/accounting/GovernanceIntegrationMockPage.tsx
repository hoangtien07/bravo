import { ArrowLeft, LockKeyhole, ShieldAlert } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Badge, Button, Card } from "@/components/ui";

const rows = [
  ["Demo mode", "Synthetic-only", "No customer or live BRAVO data"],
  ["Model egress", "Denied", "Owner must pin model/version before enabling"],
  ["Audit export", "Privacy-minimized JSON", "No raw evidence rows retained"],
  ["Capabilities", "Bank · Voucher · Period Close", "Flags cannot widen authorization"],
];

export function GovernanceIntegrationMockPage() {
  const nav = useNavigate();
  return <div className="flex-1 overflow-auto bg-background"><header className="flex items-center gap-2 border-b border-border px-4 py-2"><Button variant="ghost" size="icon" onClick={() => nav("/accounting-work")} aria-label="quay lại"><ArrowLeft className="h-4 w-4" /></Button><h1 className="font-semibold">Governance & Integration</h1><Badge tone="warn">Mock · non-functional</Badge></header>
    <main className="mx-auto max-w-4xl p-5 space-y-4"><Card className="p-5"><div className="flex gap-3"><ShieldAlert className="h-5 w-5 text-warning shrink-0" /><div><h2 className="font-semibold">Không có live control trong demonstrator</h2><p className="mt-1 text-sm text-muted-foreground">Màn hình này chỉ biểu diễn config-as-code đã freeze. Không thay đổi connector, model, role, policy hay BRAVO ERP.</p></div></div></Card>
      <Card className="overflow-hidden"><table className="w-full text-sm"><thead className="bg-muted text-left text-muted-foreground"><tr><th className="p-3">Control</th><th className="p-3">Trạng thái</th><th className="p-3">Boundary</th></tr></thead><tbody>{rows.map(([label, status, boundary]) => <tr key={label} className="border-t"><td className="p-3 font-medium">{label}</td><td className="p-3"><Badge tone={status === "Denied" ? "warn" : "primary"}>{status}</Badge></td><td className="p-3 text-muted-foreground">{boundary}</td></tr>)}</tbody></table></Card>
      <Card className="p-4 text-sm text-muted-foreground flex gap-2"><LockKeyhole className="h-4 w-4 text-primary shrink-0" />Để chuyển thành vận hành thật cần owner/operator authority, model policy, identity/egress/retention/recovery evidence và một ADR cho real data.</Card>
    </main></div>;
}
