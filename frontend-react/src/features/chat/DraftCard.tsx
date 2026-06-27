import { Check, Download, X } from "lucide-react";
import { Badge, Button, Card } from "@/components/ui";
import { downloadFile } from "@/api/client";
import { fmtMoney } from "@/lib/utils";
import type { JournalPayload } from "@/api/types";

interface Props {
  payload: JournalPayload;
  draftId?: string;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  readOnly?: boolean;
}

// Bút toán nháp — port từ frontend/app.js renderJournal (nguồn render journal duy nhất).
export function DraftCard({ payload, draftId, onApprove, onReject, readOnly }: Props) {
  if (!payload?.lines) return null;
  const balanced = payload.total_debit === payload.total_credit;
  const inv = (payload.invoice || {}) as Record<string, string>;
  return (
    <Card className="p-3 my-2">
      <div className="text-xs text-muted-foreground mb-1">
        HĐ {inv.ky_hieu}-{inv.so_hoa_don} · NCC MST {inv.mst_ban}
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-muted-foreground">
            <th className="py-1">Nợ</th>
            <th>Có</th>
            <th>Diễn giải</th>
            <th className="text-right">Số tiền</th>
          </tr>
        </thead>
        <tbody>
          {payload.lines.map((l, i) => {
            const isDebit = Number(l.debit) > 0;
            return (
              <tr key={i} className="border-t border-border">
                <td className="py-1">{isDebit ? `Nợ ${l.account}` : ""}</td>
                <td>{!isDebit ? `Có ${l.account}` : ""}</td>
                <td className="text-muted-foreground">{l.memo}</td>
                <td className="text-right tabular">{fmtMoney(isDebit ? l.debit : l.credit)}</td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr className="border-t border-border font-semibold">
            <td colSpan={3} className="py-1">Tổng</td>
            <td className="text-right tabular">{fmtMoney(payload.total_debit)}</td>
          </tr>
        </tfoot>
      </table>
      <div className="flex items-center gap-2 mt-2 flex-wrap">
        <Badge tone={balanced ? "ok" : "warn"}>{balanced ? "✓ cân Nợ=Có" : "✗ KHÔNG cân"}</Badge>
        <Badge tone={payload.needs_review ? "warn" : "ok"}>
          {payload.needs_review ? "⚠ cần kế toán xem" : "✓ tự động"}
        </Badge>
        {(payload.validation_flags || []).map((f, i) => (
          <Badge key={i} tone="warn">⚠ {f}</Badge>
        ))}
      </div>
      {!readOnly && draftId && (
        <div className="flex gap-2 mt-3 flex-wrap">
          <Button size="sm" onClick={() => onApprove?.(draftId)}>
            <Check className="h-4 w-4" /> Duyệt
          </Button>
          <Button size="sm" variant="destructive" onClick={() => onReject?.(draftId)}>
            <X className="h-4 w-4" /> Từ chối
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              downloadFile(`/api/drafts/${draftId}/export?fmt=csv`, `buttoan_${draftId.slice(0, 8)}.csv`)
                .catch((e) => alert(e instanceof Error ? e.message : "Lỗi xuất file"))
            }
          >
            <Download className="h-4 w-4" /> Xuất CSV
          </Button>
        </div>
      )}
    </Card>
  );
}
