import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Crosshair, FileText, Maximize2, MessageSquare, RefreshCw, RotateCcw, Search, X, ZoomIn, ZoomOut,
} from "lucide-react";
import { api, authHeaders } from "@/api/client";
import { Button, Spinner } from "@/components/ui";
import { useChat } from "@/store/chat";

// react-force-graph-2d nạp ĐỘNG -> tách chunk lazy (pattern MermaidBlock).
const ForceGraph2D = lazy(() => import("react-force-graph-2d"));

interface GNode { id: string; label: string; group?: string; size: number }
interface GEdge { source: string; target: string; weight: number }
interface GraphData { nodes: GNode[]; edges: GEdge[] }

const GROUP_COLORS: Record<string, string> = {
  "Cẩm nang nghiệp vụ": "#c2652a",
  "Tài liệu kỹ thuật": "#2c6e2c",
  "BI / Báo cáo": "#b08718",
  "Khác": "#8a7d70",
};
const labelColor = () =>
  document.documentElement.classList.contains("dark") ? "#e8ddcf" : "#3a302a";

export function GraphView() {
  const nav = useNavigate();
  const { newConversation, send } = useChat();
  const wrapRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<any>(null);
  const nodeObjs = useRef<Map<string, any>>(new Map());
  const [dims, setDims] = useState({ w: 800, h: 600 });
  const [raw, setRaw] = useState<GraphData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [minSim, setMinSim] = useState(0.8);
  const [query, setQuery] = useState("");
  const [sel, setSel] = useState<any>(null);

  const load = () => {
    setRaw(null); setErr(null);
    api<GraphData>("/api/graph").then(setRaw).catch((e) =>
      setErr(e instanceof Error ? e.message : "Lỗi tải đồ thị"));
  };
  useEffect(() => { load(); }, []);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setDims({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    return () => ro.disconnect();
  }, [raw]);

  useEffect(() => {
    if (!raw) return;
    const t = setTimeout(() => {
      const fg = fgRef.current;
      if (fg?.d3Force) {
        fg.d3Force("charge")?.strength(-220);
        fg.d3Force("link")?.distance(70);
        fg.d3ReheatSimulation?.();
      }
    }, 300);
    return () => clearTimeout(t);
  }, [raw]);

  // Dữ liệu ĐÃ LỌC (theo nhóm ẩn + ngưỡng liên kết). Giữ ref node ổn định để không mất vị trí.
  const graph = useMemo(() => {
    if (!raw) return { nodes: [], links: [] };
    const nodes = raw.nodes
      .filter((n) => !hidden.has(n.group || "Khác"))
      .map((n) => {
        const o = nodeObjs.current.get(n.id) || {};
        Object.assign(o, {
          id: n.id, label: n.label, group: n.group, val: Math.max(1, n.size),
          color: GROUP_COLORS[n.group || "Khác"] || "#8a7d70",
        });
        nodeObjs.current.set(n.id, o);
        return o;
      });
    const vis = new Set(nodes.map((n) => n.id));
    const links = raw.edges
      .filter((e) => e.weight >= minSim && vis.has(e.source) && vis.has(e.target))
      .map((e) => ({ source: e.source, target: e.target, weight: e.weight }));
    return { nodes, links };
  }, [raw, hidden, minSim]);

  const degree = sel
    ? graph.links.filter((l: any) => (l.source.id ?? l.source) === sel.id || (l.target.id ?? l.target) === sel.id).length
    : 0;

  // --- thao tác ---
  const zoomBy = (f: number) => { const fg = fgRef.current; if (fg) fg.zoom(fg.zoom() * f, 300); };
  const fit = () => fgRef.current?.zoomToFit(400, 40);
  const relayout = () => fgRef.current?.d3ReheatSimulation?.();
  const focusNode = () => {
    const q = query.trim().toLowerCase();
    if (!q) return;
    const n: any = graph.nodes.find((x: any) => x.label.toLowerCase().includes(q));
    if (n && n.x != null) {
      fgRef.current?.centerAt(n.x, n.y, 600);
      fgRef.current?.zoom(4, 600);
      setSel(n);
    }
  };
  const toggleGroup = (g: string) =>
    setHidden((h) => { const s = new Set(h); s.has(g) ? s.delete(g) : s.add(g); return s; });
  const locate = (n: any) => {
    if (n?.x != null) { fgRef.current?.centerAt(n.x, n.y, 600); fgRef.current?.zoom(4, 600); }
  };
  const askAI = (n: any) => { newConversation(); nav("/"); setTimeout(() => send(`Cho tôi biết về "${n.label}"`), 60); };
  const openFile = async (n: any) => {
    const win = window.open("", "_blank");
    try {
      const res = await fetch(`/api/sources/${n.id}/file`, { headers: authHeaders() });
      if (!res.ok) throw new Error();
      const url = URL.createObjectURL(await res.blob());
      if (win) win.location.href = url; else window.open(url, "_blank");
    } catch { win?.close(); alert("Không mở được file nguồn của tài liệu này."); }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <header className="border-b border-border px-4 py-2 space-y-2">
        <div>
          <h1 className="font-semibold tracking-tight">Bản đồ tri thức</h1>
          <p className="text-xs text-muted-foreground">
            Node = tài liệu (cỡ = số đoạn); cạnh nối tài liệu tương đồng nội dung. Bấm node để xem thao tác.
          </p>
        </div>
        {/* Thanh công cụ */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center gap-1 rounded-md border border-border px-2 py-1">
            <Search className="h-3.5 w-3.5 text-muted-foreground" />
            <input
              value={query} onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && focusNode()}
              placeholder="Tìm & định vị tài liệu…" className="bg-transparent outline-none w-44"
            />
          </div>
          <div className="flex items-center gap-1.5" title="Chỉ hiện liên kết có độ tương đồng ≥ ngưỡng">
            <span className="text-muted-foreground">Liên kết ≥</span>
            <input type="range" min={0.6} max={0.95} step={0.01} value={minSim}
                   onChange={(e) => setMinSim(Number(e.target.value))} className="accent-primary" />
            <span className="tabular w-9">{Math.round(minSim * 100)}%</span>
          </div>
          <div className="ml-auto flex items-center gap-1">
            <Button size="icon" variant="outline" onClick={() => zoomBy(1.4)} aria-label="phóng to"><ZoomIn className="h-4 w-4" /></Button>
            <Button size="icon" variant="outline" onClick={() => zoomBy(1 / 1.4)} aria-label="thu nhỏ"><ZoomOut className="h-4 w-4" /></Button>
            <Button size="icon" variant="outline" onClick={fit} aria-label="vừa khung"><Maximize2 className="h-4 w-4" /></Button>
            <Button size="icon" variant="outline" onClick={relayout} aria-label="sắp lại"><RotateCcw className="h-4 w-4" /></Button>
            <Button size="icon" variant="outline" onClick={load} aria-label="tải lại"><RefreshCw className="h-4 w-4" /></Button>
          </div>
          <span className="w-full sm:w-auto text-muted-foreground">
            {graph.nodes.length} tài liệu · {graph.links.length} liên kết
          </span>
        </div>
      </header>

      <div ref={wrapRef} className="flex-1 min-h-0 relative">
        {err && <div className="p-4 text-destructive text-sm">{err}</div>}
        {!raw && !err && (
          <div className="p-6 flex items-center gap-2 text-muted-foreground"><Spinner /> Đang dựng đồ thị…</div>
        )}
        {raw && (
          <>
            <Suspense fallback={<div className="p-6"><Spinner /></div>}>
              <ForceGraph2D
                ref={fgRef}
                width={dims.w} height={dims.h}
                graphData={graph}
                nodeRelSize={4}
                linkColor={() => "rgba(140,125,112,0.30)"}
                linkWidth={(l: any) => Math.max(0.4, (l.weight - 0.75) * 6)}
                cooldownTicks={140}
                backgroundColor="rgba(0,0,0,0)"
                onNodeClick={(n: any) => setSel(n)}
                nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, scale: number) => {
                  const r = Math.max(3, Math.sqrt(node.val)) * 1.1;
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
                  ctx.fillStyle = node.color;
                  ctx.fill();
                  ctx.lineWidth = (sel && sel.id === node.id ? 2 : 0.6) / scale;
                  ctx.strokeStyle = sel && sel.id === node.id ? "#c2652a" : "rgba(255,255,255,0.65)";
                  ctx.stroke();
                  const fs = Math.max(2.5, 11 / scale);
                  ctx.font = `${fs}px system-ui, sans-serif`;
                  ctx.textAlign = "center";
                  ctx.textBaseline = "top";
                  ctx.fillStyle = labelColor();
                  const label = node.label.length > 34 ? node.label.slice(0, 33) + "…" : node.label;
                  ctx.fillText(label, node.x, node.y + r + 1.5 / scale);
                }}
                nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
                  const r = Math.max(3, Math.sqrt(node.val)) * 1.1 + 3;
                  ctx.fillStyle = color;
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
                  ctx.fill();
                }}
              />
            </Suspense>

            {/* Panel chi tiết + nút thao tác */}
            {sel && (
              <aside className="absolute top-2 left-2 w-64 rounded-md border border-border bg-card/95 p-3 shadow-card text-sm">
                <div className="flex items-start justify-between gap-2">
                  <div className="font-medium break-words">{sel.label}</div>
                  <button onClick={() => setSel(null)} aria-label="đóng"><X className="h-4 w-4" /></button>
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {sel.group} · {sel.val} đoạn · {degree} liên kết
                </div>
                <div className="mt-3 flex flex-col gap-2">
                  <Button size="sm" onClick={() => openFile(sel)}><FileText className="h-4 w-4" /> Mở file gốc</Button>
                  <Button size="sm" variant="outline" onClick={() => askAI(sel)}><MessageSquare className="h-4 w-4" /> Hỏi AI về tài liệu</Button>
                  <Button size="sm" variant="ghost" onClick={() => locate(sel)}><Crosshair className="h-4 w-4" /> Định vị</Button>
                </div>
              </aside>
            )}

            {/* Chú giải — bấm để ẩn/hiện nhóm */}
            <div className="absolute top-2 right-2 rounded-md border border-border bg-card/90 p-2 text-xs space-y-1">
              <div className="text-muted-foreground mb-1">Bấm để lọc nhóm</div>
              {Object.entries(GROUP_COLORS).map(([g, c]) => (
                <button key={g} onClick={() => toggleGroup(g)}
                        className={"flex items-center gap-1.5 w-full " + (hidden.has(g) ? "opacity-40 line-through" : "")}>
                  <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: c }} />
                  {g}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
