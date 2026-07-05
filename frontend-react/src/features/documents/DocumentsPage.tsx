import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, FileText, Upload } from "lucide-react";
import { api, authHeaders } from "@/api/client";
import { Badge, Button, Card } from "@/components/ui";

interface SourceOut {
  id: string;
  filename: string;
  status: string;
  knowledge_type: string | null;
}
const STATUS_TONE: Record<string, "muted" | "ok" | "warn"> = {
  ready: "ok", pending: "warn", failed: "muted",
};

// Nạp tài liệu tri thức qua UI (W1.7) — helpdesk tự mở rộng KB, không cần chạy script.
// Backend POST /api/sources (cần quyền doc:create); ingest đồng bộ (parse->chunk->embed->RLS).
export function DocumentsPage() {
  const [sources, setSources] = useState<SourceOut[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [ktype, setKtype] = useState("");
  const nav = useNavigate();

  const load = () =>
    api<SourceOut[]>("/api/sources").then(setSources).catch(() => setSources([]));
  useEffect(() => { load(); }, []);

  const upload = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true);
    let ok = 0; const errs: string[] = [];
    for (const f of Array.from(files)) {
      const fd = new FormData();
      fd.append("file", f);
      if (ktype) fd.append("knowledge_type", ktype);
      try {
        const r = await fetch("/api/sources", { method: "POST", headers: authHeaders(), body: fd });
        if (r.ok) ok++;
        else errs.push(`${f.name}: ${(await r.json().catch(() => ({}))).detail || r.status}`);
      } catch (e) {
        errs.push(`${f.name}: ${e instanceof Error ? e.message : "lỗi"}`);
      }
    }
    setBusy(false);
    setMsg(`Đã nạp ${ok} tài liệu${errs.length ? `. Lỗi: ${errs.join("; ")}` : "."}`);
    load();
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2">
        <Button variant="ghost" size="icon" onClick={() => nav("/")} aria-label="quay lại"><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="font-semibold tracking-tight flex items-center gap-2">
          <FileText className="h-4 w-4" /> Tài liệu tri thức
        </h1>
      </header>

      <div className="mx-auto max-w-3xl p-4 space-y-4">
        <Card className="p-6 text-center border-dashed">
          <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
          <p className="text-sm text-muted-foreground my-2">
            Thả/chọn tài liệu (PDF/DOCX/XLSX/TXT) — hệ bóc tách, chia đoạn, nhúng vector và áp
            phân quyền phòng ban. Sau khi nạp, hỏi ở khung Chat sẽ có trích dẫn trang.
          </p>
          <input
            value={ktype} onChange={(e) => setKtype(e.target.value)}
            placeholder="Nhãn loại tài liệu (tuỳ chọn, vd: cam_nang, quy_trinh)"
            className="mb-3 w-full max-w-sm rounded-md border border-border bg-transparent px-3 py-1.5 text-sm"
          />
          <div>
            <label className="inline-block">
              <input type="file" accept=".pdf,.docx,.xlsx,.txt" multiple className="hidden"
                     onChange={(e) => upload(e.target.files)} />
              <span className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm cursor-pointer hover:bg-primary/90">
                {busy ? "Đang nạp…" : "Chọn tài liệu"}
              </span>
            </label>
          </div>
          {msg && <p className="text-xs text-muted-foreground mt-2 break-words">{msg}</p>}
        </Card>

        <div className="space-y-1">
          {sources.map((s) => (
            <div key={s.id} className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm">
              <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
              <span className="flex-1 truncate">{s.filename}</span>
              {s.knowledge_type && <span className="text-xs text-muted-foreground">{s.knowledge_type}</span>}
              <Badge tone={STATUS_TONE[s.status] || "muted"}>{s.status}</Badge>
            </div>
          ))}
          {!sources.length && <p className="text-sm text-muted-foreground">Chưa có tài liệu nào bạn được phép xem.</p>}
        </div>
      </div>
    </div>
  );
}
