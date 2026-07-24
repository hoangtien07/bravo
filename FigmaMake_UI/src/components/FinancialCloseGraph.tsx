import { useEffect, useState } from "react";
import { DiagonalMotif, StatusBadge, T, IllustrationLabel } from "./shared";
import type { EvidenceStatus } from "./shared";
import { useApp } from "../context/AppContext";
import { useQA } from "../context/QAContext";

interface GraphNode {
  id: string;
  type: "outcome" | "prerequisite" | "operation" | "evidence" | "missing";
  label: string;
  sublabel?: string;
  status: EvidenceStatus;
  col: number;
  row: number;
  detail: {
    reason: string;
    evidenceScope: string;
    responsible: string;
  };
}

type GraphEdge = { from: string; to: string; status: "verified" | "pending" | "conflict" };
type ViewMode = "graph" | "list" | "table";
type FilterVal = "all" | "conflict" | "missing" | "ready" | "in-progress" | "not-assessed";

// Illustration nodes — no specific financial amounts or dates
const NODES: GraphNode[] = [
  { id: "outcome",  type: "outcome",      label: "Báo cáo tài chính",       sublabel: "Kết quả cuối kỳ — minh họa",  status: "in-progress",  col: 4, row: 2,
    detail: { reason: "Các điều kiện tiên quyết chưa đủ — minh họa", evidenceScope: "[Chưa xác định]", responsible: "Kế toán trưởng" } },

  { id: "prereq-1", type: "prerequisite", label: "Chứng từ gốc",            sublabel: "Đang xử lý — minh họa",       status: "in-progress",  col: 3, row: 1,
    detail: { reason: "Một số chứng từ chưa được phê duyệt — minh họa", evidenceScope: "[Nhật ký chung — minh họa]", responsible: "Kế toán viên" } },
  { id: "prereq-2", type: "prerequisite", label: "Đối chiếu sổ phụ",        sublabel: "Xung đột — minh họa",         status: "conflict",     col: 3, row: 2,
    detail: { reason: "Chênh lệch công nợ chưa được giải trình — minh họa", evidenceScope: "[Sổ chi tiết công nợ — minh họa]", responsible: "Kế toán công nợ" } },
  { id: "prereq-3", type: "prerequisite", label: "Nghiệp vụ định kỳ",       sublabel: "Phân bổ chưa duyệt — minh họa", status: "in-progress", col: 3, row: 3,
    detail: { reason: "Phân bổ chi phí trả trước chưa phê duyệt — minh họa", evidenceScope: "[Bảng phân bổ — minh họa]", responsible: "Kế toán tổng hợp" } },
  { id: "prereq-4", type: "prerequisite", label: "Kiểm kê tồn kho",         sublabel: "Thiếu biên bản — minh họa",   status: "missing",      col: 3, row: 4,
    detail: { reason: "Biên bản kiểm kê kho chưa được cung cấp — minh họa", evidenceScope: "[Chưa có]", responsible: "Kế toán kho" } },

  { id: "op-1",    type: "operation",    label: "Duyệt hóa đơn BRAVO",     sublabel: "Kiểm soát mua hàng — minh họa", status: "in-progress", col: 2, row: 1,
    detail: { reason: "Một số hóa đơn đang chờ duyệt — minh họa", evidenceScope: "[Module Mua hàng — minh họa]", responsible: "Kế toán viên" } },
  { id: "op-2",    type: "operation",    label: "Đối chiếu công nợ",        sublabel: "Module AR/AP — minh họa",      status: "conflict",     col: 2, row: 2,
    detail: { reason: "Xung đột số dư với đối tác — minh họa", evidenceScope: "[Module Công nợ — minh họa]", responsible: "Kế toán công nợ" } },
  { id: "op-3",    type: "operation",    label: "Tính khấu hao TSCĐ",       sublabel: "Đã hoàn thành — minh họa",    status: "ready",        col: 2, row: 3,
    detail: { reason: "Khấu hao đã được tính và phê duyệt — minh họa", evidenceScope: "[Module TSCĐ — minh họa]", responsible: "Kế toán TSCĐ" } },

  { id: "ev-1",    type: "evidence",     label: "Nhật ký chung",            sublabel: "Đã xác minh — minh họa",      status: "ready",        col: 1, row: 1,
    detail: { reason: "Chứng từ đã hạch toán và phê duyệt — minh họa", evidenceScope: "[Trang — minh họa]", responsible: "Kế toán viên" } },
  { id: "ev-2",    type: "evidence",     label: "Sổ chi tiết công nợ",      sublabel: "Xung đột — minh họa",         status: "conflict",     col: 1, row: 2,
    detail: { reason: "Chênh lệch chưa được giải trình — minh họa", evidenceScope: "[Đối tác — minh họa]", responsible: "Kế toán công nợ" } },
  { id: "ev-3",    type: "evidence",     label: "Bảng khấu hao",            sublabel: "Đã xác minh — minh họa",      status: "ready",        col: 1, row: 3,
    detail: { reason: "Khấu hao đã phê duyệt và khớp — minh họa", evidenceScope: "[Bảng tính — minh họa]", responsible: "Kế toán TSCĐ" } },
  { id: "ev-4",    type: "missing",      label: "Biên bản kiểm kê kho",     sublabel: "Chưa cung cấp — minh họa",    status: "missing",      col: 1, row: 4,
    detail: { reason: "Biên bản kiểm kê vật lý còn thiếu — minh họa", evidenceScope: "[Chưa có]", responsible: "Kế toán kho" } },
];

const EDGES: GraphEdge[] = [
  { from: "ev-1",    to: "op-1",    status: "pending" },
  { from: "ev-2",    to: "op-2",    status: "conflict" },
  { from: "ev-3",    to: "op-3",    status: "verified" },
  { from: "ev-4",    to: "prereq-4", status: "pending" },
  { from: "op-1",    to: "prereq-1", status: "pending" },
  { from: "op-2",    to: "prereq-2", status: "conflict" },
  { from: "op-3",    to: "prereq-3", status: "verified" },
  { from: "prereq-1", to: "outcome", status: "pending" },
  { from: "prereq-2", to: "outcome", status: "conflict" },
  { from: "prereq-3", to: "outcome", status: "pending" },
  { from: "prereq-4", to: "outcome", status: "pending" },
];

const COL_LABELS = ["", "Bằng chứng", "Kiểm soát BRAVO", "Điều kiện tiên quyết", "Kết quả"];
const COL_X = [0, 80, 260, 460, 660];
const ROW_H = 90;
const NODE_W = 160;
const NODE_H = 56;

const TYPE_LABELS: Record<GraphNode["type"], string> = {
  outcome:      "Kết quả",
  prerequisite: "Điều kiện tiên quyết",
  operation:    "Kiểm soát BRAVO",
  evidence:     "Bằng chứng",
  missing:      "Thiếu thông tin",
};

function nodeCenter(n: GraphNode) {
  return { x: COL_X[n.col] + NODE_W / 2, y: n.row * ROW_H + NODE_H / 2 };
}

export default function FinancialCloseGraph() {
  const { state } = useApp();
  const { qa } = useQA();

  const [width, setWidth] = useState(window.innerWidth);
  useEffect(() => {
    const h = () => setWidth(window.innerWidth);
    window.addEventListener("resize", h);
    return () => window.removeEventListener("resize", h);
  }, []);
  const isMobile = width < 768;

  const [view, setView] = useState<ViewMode>(isMobile ? "list" : "graph");
  const [filter, setFilter] = useState<FilterVal>("all");
  const [selected, setSelected] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (isMobile) setView("list");
  }, [isMobile]);

  const selectedNode = NODES.find(n => n.id === selected);
  const scopeKnown = state.scope.company.known && state.scope.accountingPeriod.known;

  const filteredNodes = NODES.filter(n => {
    const matchFilter = filter === "all" || n.status === filter;
    const matchSearch = !search || n.label.toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });
  const filteredIds = new Set(filteredNodes.map(n => n.id));

  const svgH = 5 * ROW_H + 40;
  const svgW = COL_X[4] + NODE_W + 40;

  const FILTERS: { v: FilterVal; label: string }[] = [
    { v: "all", label: "Tất cả" },
    { v: "ready", label: "Sẵn sàng" },
    { v: "conflict", label: "Xung đột" },
    { v: "missing", label: "Thiếu" },
    { v: "in-progress", label: "Đang xử lý" },
  ];

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      {/* Toolbar */}
      <div style={{ padding: "10px 20px", borderBottom: `1px solid ${T.border}`, background: T.white, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
        <DiagonalMotif size={13} color={T.green} />
        <span style={{ fontSize: 13, fontWeight: 600, color: T.strong }}>Sơ đồ bằng chứng đóng kỳ</span>

        {!scopeKnown && (
          <span style={{ fontSize: 11, color: "#92400E", background: T.warnSurface, borderRadius: 4, padding: "2px 8px" }}>
            Phạm vi chưa xác định — dữ liệu minh họa
          </span>
        )}

        <div style={{ display: "flex", gap: 4, marginLeft: "auto" }}>
          {(["graph", "list", "table"] as ViewMode[]).map(v => (
            <button key={v} onClick={() => setView(v)} aria-pressed={view === v} style={{ fontSize: 12, padding: "4px 10px", borderRadius: 6, border: `1px solid ${T.border}`, background: view === v ? T.softTeal : T.white, color: view === v ? T.interactive : T.secondary, cursor: "pointer", fontFamily: "inherit", minHeight: 32 }}>
              {v === "graph" ? "⊡ Sơ đồ" : v === "list" ? "☰ Danh sách" : "⊟ Bảng"}
            </button>
          ))}
        </div>
      </div>

      {/* Filters + search */}
      <div style={{ padding: "8px 20px", borderBottom: `1px solid ${T.border}`, background: T.canvas, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Tìm nút..." aria-label="Tìm kiếm nút trong sơ đồ" style={{ padding: "4px 10px", border: `1px solid ${T.border}`, borderRadius: 6, fontSize: 12, fontFamily: "inherit", color: T.strong, background: T.white, minHeight: 32, width: 180 }} />
        {FILTERS.map(f => (
          <button key={f.v} onClick={() => setFilter(f.v)} style={{ fontSize: 12, padding: "4px 10px", borderRadius: 6, border: `1px solid ${T.border}`, background: filter === f.v ? T.softTeal : T.white, color: filter === f.v ? T.interactive : T.secondary, cursor: "pointer", fontFamily: "inherit", minHeight: 32 }}>{f.label}</button>
        ))}
        {qa.enabled && <IllustrationLabel />}
      </div>

      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {/* Main content */}
        <div style={{ flex: 1, overflow: "auto" }}>
          {view === "graph" && (
            <div style={{ padding: 24 }}>
              {/* Column labels */}
              <div style={{ display: "flex", gap: 0, marginBottom: 8, minWidth: svgW }}>
                {COL_LABELS.slice(1).map((l, i) => (
                  <div key={l} style={{ width: NODE_W + (COL_X[i + 2] ?? COL_X[i + 1] + NODE_W + 20) - COL_X[i + 1], fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.lightGray, paddingLeft: 0, flexShrink: 0 }}>
                    {l}
                  </div>
                ))}
              </div>
              <div style={{ position: "relative", minWidth: svgW }}>
                <svg width={svgW} height={svgH} style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none", overflow: "visible" }} aria-hidden="true">
                  {EDGES.map((e, i) => {
                    const from = NODES.find(n => n.id === e.from);
                    const to   = NODES.find(n => n.id === e.to);
                    if (!from || !to) return null;
                    const a = nodeCenter(from);
                    const b = nodeCenter(to);
                    const midX = (a.x + b.x) / 2;
                    const edgeColor = e.status === "verified" ? T.green : e.status === "conflict" ? T.error : T.border;
                    const dim = !filteredIds.has(e.from) || !filteredIds.has(e.to);
                    return (
                      <g key={i} opacity={dim ? 0.15 : 1}>
                        <path d={`M ${a.x + NODE_W / 2} ${a.y} C ${midX} ${a.y}, ${midX} ${b.y}, ${b.x - NODE_W / 2} ${b.y}`} fill="none" stroke={edgeColor} strokeWidth={1.5} strokeDasharray={e.status === "pending" ? "4 3" : undefined} />
                        <text x={midX} y={(a.y + b.y) / 2 - 3} fontSize={9} fill={edgeColor} textAnchor="middle" transform={`rotate(29, ${midX}, ${(a.y + b.y) / 2})`}>//</text>
                      </g>
                    );
                  })}
                </svg>
                <div style={{ position: "relative", width: svgW, height: svgH }} role="list" aria-label="Các nút trong sơ đồ bằng chứng">
                  {NODES.map(node => {
                    const { x, y } = nodeCenter(node);
                    const dim = !filteredIds.has(node.id);
                    return (
                      <GraphNodeEl key={node.id} node={node} x={x - NODE_W / 2} y={y - NODE_H / 2} selected={selected === node.id} dim={dim} onClick={() => setSelected(selected === node.id ? null : node.id)} />
                    );
                  })}
                </div>
              </div>
              <p style={{ marginTop: 12, fontSize: 11, color: T.lightGray, fontStyle: "italic" }}>Dữ liệu minh họa. Nhấn vào nút để xem chi tiết. Nhấn lại để bỏ chọn.</p>
            </div>
          )}

          {view === "list" && (
            <div style={{ padding: "16px 20px", maxWidth: 760 }}>
              <p style={{ margin: "0 0 16px", fontSize: 13, color: T.secondary }}>Hiển thị {filteredNodes.length}/{NODES.length} nút</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }} role="list" aria-label="Danh sách các nút bằng chứng">
                {filteredNodes.length === 0 ? (
                  <p style={{ color: T.secondary, fontSize: 13, fontStyle: "italic" }}>Không có nút nào khớp với bộ lọc.</p>
                ) : filteredNodes.map(node => (
                  <button
                    key={node.id}
                    role="listitem"
                    onClick={() => setSelected(selected === node.id ? null : node.id)}
                    aria-pressed={selected === node.id}
                    style={{ display: "flex", alignItems: "flex-start", gap: 12, padding: "12px 14px", background: selected === node.id ? T.softTeal : T.white, border: `1px solid ${selected === node.id ? T.green : T.border}`, borderRadius: 8, cursor: "pointer", textAlign: "left", fontFamily: "inherit", width: "100%", transition: "border-color 150ms" }}
                  >
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: T.secondary, flexShrink: 0 }}>{TYPE_LABELS[node.type]}</span>
                        <span style={{ fontSize: 12, fontWeight: 500, color: T.strong }}>{node.label}</span>
                      </div>
                      {node.sublabel && <p style={{ margin: "0 0 4px", fontSize: 12, color: T.secondary }}>{node.sublabel}</p>}
                      <p style={{ margin: 0, fontSize: 12, color: T.lightGray }}>Phụ trách: {node.detail.responsible}</p>
                    </div>
                    <StatusBadge status={node.status} compact />
                  </button>
                ))}
              </div>
            </div>
          )}

          {view === "table" && (
            <div style={{ padding: "16px 20px", overflowX: "auto" }}>
              <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 13 }} aria-label="Bảng các nút bằng chứng">
                <thead>
                  <tr style={{ background: T.canvas }}>
                    {["Loại", "Tên nút", "Ghi chú", "Phụ trách", "Trạng thái"].map(h => (
                      <th key={h} scope="col" style={{ padding: "8px 12px", textAlign: "left", fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: T.secondary, borderBottom: `2px solid ${T.border}`, whiteSpace: "nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredNodes.length === 0 ? (
                    <tr><td colSpan={5} style={{ padding: "20px 12px", color: T.secondary, fontStyle: "italic" }}>Không có dữ liệu khớp bộ lọc.</td></tr>
                  ) : filteredNodes.map((node, i) => (
                    <tr
                      key={node.id}
                      onClick={() => setSelected(selected === node.id ? null : node.id)}
                      aria-selected={selected === node.id}
                      tabIndex={0}
                      onKeyDown={e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setSelected(selected === node.id ? null : node.id); } }}
                      style={{ background: selected === node.id ? T.softTeal : i % 2 === 0 ? T.white : T.canvas, cursor: "pointer", borderBottom: `1px solid ${T.border}`, outline: "none" }}
                    >
                      <td style={{ padding: "8px 12px", color: T.secondary, whiteSpace: "nowrap" }}>{TYPE_LABELS[node.type]}</td>
                      <td style={{ padding: "8px 12px", fontWeight: 500, color: T.strong }}>{node.label}</td>
                      <td style={{ padding: "8px 12px", color: T.secondary }}>{node.sublabel ?? "—"}</td>
                      <td style={{ padding: "8px 12px", color: T.secondary, whiteSpace: "nowrap" }}>{node.detail.responsible}</td>
                      <td style={{ padding: "8px 12px" }}><StatusBadge status={node.status} compact /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Inspector panel */}
        {selectedNode && !isMobile && (
          <aside style={{ width: 320, flexShrink: 0, borderLeft: `1px solid ${T.border}`, background: T.white, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div style={{ padding: "14px 20px", borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: T.strong }}>Chi tiết nút</span>
              <button onClick={() => setSelected(null)} aria-label="Đóng chi tiết" style={{ background: "none", border: "none", color: T.secondary, cursor: "pointer", fontSize: 18, minHeight: 36, minWidth: 36, borderRadius: 4 }}>×</button>
            </div>
            <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>
              <span style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: T.secondary }}>{TYPE_LABELS[selectedNode.type]}</span>
              <h3 style={{ margin: "4px 0 10px", fontSize: 15, fontWeight: 600, color: T.strong }}>{selectedNode.label}</h3>
              <StatusBadge status={selectedNode.status} />
              <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 12 }}>
                {[
                  ["Lý do", selectedNode.detail.reason],
                  ["Phạm vi bằng chứng", selectedNode.detail.evidenceScope],
                  ["Người phụ trách", selectedNode.detail.responsible],
                ].map(([k, v]) => (
                  <div key={k}>
                    <p style={{ margin: "0 0 2px", fontSize: 11, fontWeight: 600, color: T.secondary, textTransform: "uppercase", letterSpacing: "0.06em" }}>{k}</p>
                    <p style={{ margin: 0, fontSize: 13, color: T.strong, lineHeight: "20px" }}>{v}</p>
                  </div>
                ))}
              </div>
              <p style={{ marginTop: 16, fontSize: 11, color: T.lightGray, fontStyle: "italic" }}>Dữ liệu minh họa — không phải dữ liệu thực.</p>
            </div>
          </aside>
        )}
      </div>

      {/* Mobile inspector sheet */}
      {selectedNode && isMobile && (
        <>
          <div onClick={() => setSelected(null)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.3)", zIndex: 30 }} aria-hidden="true" />
          <div role="dialog" aria-modal="true" aria-label="Chi tiết nút" style={{ position: "fixed", bottom: 0, left: 0, right: 0, background: T.white, borderRadius: "12px 12px 0 0", zIndex: 40, padding: 20, maxHeight: "60vh", overflow: "auto" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: T.strong }}>Chi tiết nút</span>
              <button onClick={() => setSelected(null)} aria-label="Đóng" style={{ background: "none", border: "none", fontSize: 20, cursor: "pointer", minHeight: 44, minWidth: 44 }}>×</button>
            </div>
            <span style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: T.secondary }}>{TYPE_LABELS[selectedNode.type]}</span>
            <h3 style={{ margin: "4px 0 10px", fontSize: 15, fontWeight: 600, color: T.strong }}>{selectedNode.label}</h3>
            <StatusBadge status={selectedNode.status} />
            <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                ["Lý do", selectedNode.detail.reason],
                ["Phạm vi bằng chứng", selectedNode.detail.evidenceScope],
                ["Người phụ trách", selectedNode.detail.responsible],
              ].map(([k, v]) => (
                <div key={k}>
                  <p style={{ margin: "0 0 2px", fontSize: 11, fontWeight: 600, color: T.secondary, textTransform: "uppercase", letterSpacing: "0.06em" }}>{k}</p>
                  <p style={{ margin: 0, fontSize: 13, color: T.strong }}>{v}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function GraphNodeEl({ node, x, y, selected, dim, onClick }: { node: GraphNode; x: number; y: number; selected: boolean; dim: boolean; onClick: () => void }) {
  const statusColors: Record<string, { border: string; bg: string; text: string }> = {
    ready:         { border: T.green,   bg: T.softTeal,      text: T.interactive },
    "in-progress": { border: T.green,   bg: T.white,         text: T.strong },
    conflict:      { border: T.error,   bg: "#FDECEA",       text: T.error },
    missing:       { border: T.orange,  bg: T.warnSurface,   text: "#92400E" },
    "not-assessed":{ border: T.border,  bg: T.white,         text: T.secondary },
  };
  const c = statusColors[node.status] ?? statusColors["not-assessed"];
  const isOutcome = node.type === "outcome";
  return (
    <button
      role="listitem"
      onClick={onClick}
      aria-pressed={selected}
      aria-label={`${TYPE_LABELS[node.type]}: ${node.label} — ${node.status}`}
      style={{
        position: "absolute", left: x, top: y, width: NODE_W, height: NODE_H,
        border: `${selected ? 2 : 1}px solid ${selected ? T.interactive : c.border}`,
        borderRadius: isOutcome ? 10 : 6,
        background: selected ? T.softTeal : c.bg,
        padding: "6px 10px", textAlign: "left", cursor: "pointer",
        opacity: dim ? 0.2 : 1,
        transition: "opacity 150ms, border-color 150ms",
        fontFamily: "inherit", display: "flex", flexDirection: "column", justifyContent: "center", gap: 2,
        boxShadow: isOutcome ? `0 2px 8px rgba(0,107,93,0.10)` : "none",
      }}
    >
      <span style={{ fontSize: 11, fontWeight: 600, color: c.text, lineHeight: "15px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{node.label}</span>
      {node.sublabel && <span style={{ fontSize: 9, color: T.lightGray, lineHeight: "13px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{node.sublabel}</span>}
    </button>
  );
}
