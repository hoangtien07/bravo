import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { FileText, MessageSquarePlus, Receipt, Trash2 } from "lucide-react";
import { api } from "@/api/client";
import { Button } from "@/components/ui";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn, fmtDate } from "@/lib/utils";
import { useAuth } from "@/store/auth";
import type { ConversationSummary } from "@/api/types";

export function ConversationSidebar() {
  const [items, setItems] = useState<ConversationSummary[]>([]);
  const { id } = useParams();
  const nav = useNavigate();
  const { identity, logout } = useAuth();

  const load = () => api<ConversationSummary[]>("/api/conversations").then(setItems).catch(() => {});
  useEffect(() => {
    load();
    const h = () => load();
    window.addEventListener("conv:refresh", h);
    return () => window.removeEventListener("conv:refresh", h);
  }, [id]);

  const del = async (cid: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    await api(`/api/conversations/${cid}`, { method: "DELETE" });
    if (id === cid) nav("/");
    load();
  };

  return (
    <aside className="w-72 shrink-0 border-r border-border bg-card/60 flex flex-col h-full">
      <div className="p-3">
        <Button className="w-full" onClick={() => nav("/")}>
          <MessageSquarePlus className="h-4 w-4" /> Hội thoại mới
        </Button>
      </div>
      <nav className="px-2 pb-2">
        <Link to="/money-engine" className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-muted">
          <Receipt className="h-4 w-4" /> Hoá đơn → bút toán
        </Link>
      </nav>
      <div className="px-3 py-1 text-xs font-medium text-muted-foreground">Lịch sử</div>
      <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {items.map((c) => (
          <Link
            key={c.id}
            to={`/c/${c.id}`}
            className={cn("group flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-muted", id === c.id && "bg-muted")}
          >
            <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="flex-1 truncate">{c.title || "Hội thoại"}</span>
            <button onClick={(e) => del(c.id, e)} className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive" aria-label="xoá">
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </Link>
        ))}
        {!items.length && <div className="px-3 py-2 text-xs text-muted-foreground">Chưa có hội thoại.</div>}
      </div>
      <div className="border-t border-border p-3 text-xs text-muted-foreground">
        <div className="truncate">{identity?.full_name}</div>
        <div className="mt-1 flex items-center justify-between">
          <button className="text-primary hover:underline" onClick={logout}>Đăng xuất</button>
          <ThemeToggle />
        </div>
      </div>
    </aside>
  );
}
