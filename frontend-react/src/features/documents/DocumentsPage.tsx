import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, FileText, Trash2, Upload } from "lucide-react";
import { Badge, Button, Card } from "@/components/ui";
import { useAuth } from "@/store/auth";
import { deleteSource, listSources, uploadSource } from "@/api/workspace";
import type { SourceItem } from "@/api/types";

const STATUS_TONE: Record<string, "muted" | "ok" | "warn"> = {
  ready: "ok", pending: "warn", failed: "muted",
};
const VIS_LABEL: Record<string, string> = {
  personal: "Cá nhân", department: "Phòng ban", global: "Công ty",
};
type Tab = "mine" | "department" | "global";

// Không gian tài liệu 3 tầng (v2): "Tài liệu của tôi" (cá nhân) / "Phòng ban" / "Công ty".
// Upload mặc định CÁ NHÂN (chỉ mình thấy). Chọn phạm vi rộng hơn cần quyền tạo tương ứng.
export function DocumentsPage() {
  const [tab, setTab] = useState<Tab>("mine");
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [ktype, setKtype] = useState("");
  const [visibility, setVisibility] = useState<"personal" | "department" | "global">("personal");
  const nav = useNavigate();
  const identity = useAuth((s) => s.identity);

  const canDept = !!identity && (identity.is_admin || identity.permissions.some((p) => p.startsWith("doc:create")));
  const canGlobal = !!identity && (identity.is_admin || identity.permissions.includes("doc:create:all"));

  const load = (t: Tab) => listSources(t).then(setSources).catch(() => setSources([]));
  useEffect(() => { load(tab); }, [tab]);

  const upload = async (files: FileList | null) => {
    if (!files?.length) return;
    setBusy(true);
    let ok = 0; const errs: string[] = [];
    for (const f of Array.from(files)) {
      try {
        await uploadSource(f, visibility, { knowledge_type: ktype || undefined });
        ok++;
      } catch (e) {
        errs.push(`${f.name}: ${e instanceof Error ? e.message : "lỗi"}`);
      }
    }
    setBusy(false);
    setMsg(`Đã nạp ${ok} tài liệu (${VIS_LABEL[visibility]})${errs.length ? `. Lỗi: ${errs.join("; ")}` : "."}`);
    // Show the tab matching where they just uploaded.
    const target: Tab = visibility === "personal" ? "mine" : visibility;
    if (target === tab) load(tab); else setTab(target);
  };

  const remove = async (s: SourceItem) => {
    if (!confirm(`Xoá "${s.filename}"? Không thể hoàn tác.`)) return;
    try {
      await deleteSource(s.id);
      load(tab);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Lỗi xoá");
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2">
        <Button variant="ghost" size="icon" onClick={() => nav("/")} aria-label="quay lại"><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="font-semibold tracking-tight flex items-center gap-2">
          <FileText className="h-4 w-4" /> Không gian tài liệu
        </h1>
      </header>

      <div className="mx-auto max-w-3xl p-4 space-y-4">
        <div className="flex gap-1 border-b border-border">
          {(["mine", "department", "global"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={
                "px-3 py-1.5 text-sm border-b-2 -mb-px " +
                (tab === t ? "border-primary text-foreground font-medium" : "border-transparent text-muted-foreground hover:text-foreground")
              }
            >
              {t === "mine" ? "Tài liệu của tôi" : t === "department" ? "Phòng ban" : "Công ty"}
            </button>
          ))}
        </div>

        <Card className="p-6 text-center border-dashed">
          <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
          <p className="text-sm text-muted-foreground my-2">
            Thả/chọn tài liệu (PDF/DOCX/XLSX/TXT/MD). Mặc định là <b>tài liệu cá nhân</b> — chỉ
            mình bạn thấy. Sau khi nạp, hỏi ở khung Chat sẽ có trích dẫn.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2 mb-3">
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value as typeof visibility)}
              className="rounded-md border border-border bg-transparent px-3 py-1.5 text-sm"
            >
              <option value="personal">Cá nhân (chỉ mình tôi)</option>
              {canDept && <option value="department">Phòng ban</option>}
              {canGlobal && <option value="global">Công ty (dùng chung)</option>}
            </select>
            <input
              value={ktype} onChange={(e) => setKtype(e.target.value)}
              placeholder="Nhãn (tuỳ chọn)"
              className="rounded-md border border-border bg-transparent px-3 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="inline-block">
              <input type="file" accept=".pdf,.docx,.xlsx,.txt,.md" multiple className="hidden"
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
              <Badge tone="muted">{VIS_LABEL[s.visibility] || s.visibility}</Badge>
              {s.knowledge_type && <span className="text-xs text-muted-foreground">{s.knowledge_type}</span>}
              <Badge tone={STATUS_TONE[s.status] || "muted"}>{s.status}</Badge>
              {(s.owned || s.visibility !== "personal") && (
                <button aria-label={`xoá ${s.filename}`} className="p-1 rounded text-muted-foreground hover:text-destructive hover:bg-muted" onClick={() => remove(s)}>
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ))}
          {!sources.length && <p className="text-sm text-muted-foreground">Chưa có tài liệu nào trong mục này.</p>}
        </div>
      </div>
    </div>
  );
}
