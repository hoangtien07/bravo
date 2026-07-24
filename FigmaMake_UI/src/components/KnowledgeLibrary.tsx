import React, { useState } from "react";
import { Button, T, EmptyState, SkeletonBlock, Banner, IllustrationLabel } from "./shared";
import { useQA } from "../context/QAContext";
import { KNOWLEDGE_ILLUSTRATION } from "../fixtures/scenarios";
import type { KnowledgeDoc, DocType } from "../state/types";

const TYPE_COLORS: Record<DocType, { bg: string; text: string }> = {
  "Quy trình nội bộ":     { bg: T.softTeal,      text: T.interactive },
  "Văn bản pháp lý":      { bg: "#EFF6FF",        text: "#175CD3"    },
  "Hướng dẫn BRAVO":      { bg: "#F0FDF4",        text: "#166534"    },
  "Bằng chứng kiểm toán": { bg: T.warnSurface,    text: "#92400E"    },
};

const APPROVAL_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  approved:      { label: "Đã phê duyệt",  color: T.interactive, bg: T.softTeal     },
  draft:         { label: "Bản nháp",      color: "#92400E",     bg: T.warnSurface  },
  conflict:      { label: "Xung đột",      color: T.error,       bg: T.errorSurface },
  not_available: { label: "Chưa có",       color: T.lightGray,   bg: T.canvas       },
};
const INGESTION_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  completed:      { label: "Đã nạp",           color: T.interactive, bg: T.softTeal    },
  in_progress:    { label: "Đang nạp",          color: T.interactive, bg: T.softTeal    },
  failed:         { label: "Nạp thất bại",      color: T.error,       bg: T.errorSurface },
  missing:        { label: "Chưa có tài liệu",  color: "#92400E",     bg: T.warnSurface },
  not_applicable: { label: "Không áp dụng",     color: T.lightGray,   bg: T.canvas      },
};

export default function KnowledgeLibrary() {
  const { qa } = useQA();
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [width, setWidth] = useState(window.innerWidth);
  React.useEffect(() => {
    const h = () => setWidth(window.innerWidth);
    window.addEventListener("resize", h);
    return () => window.removeEventListener("resize", h);
  }, []);
  const isMobile = width < 768;

  if (qa.componentState === "loading") {
    return <div style={{ flex: 1, padding: 32 }}><SkeletonBlock /></div>;
  }

  const docs = KNOWLEDGE_ILLUSTRATION;
  const filtered = docs.filter(d => {
    const q = search.toLowerCase();
    const matchSearch = d.name.toLowerCase().includes(q) || d.owner.toLowerCase().includes(q);
    return matchSearch && (filterType === "all" || d.type === filterType);
  });
  const selectedDoc = docs.find(d => d.id === selectedId);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      {/* Toolbar */}
      <div style={{ padding: "12px 20px", borderBottom: `1px solid ${T.border}`, background: T.white, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: T.strong }}>Kho tri thức</span>
        <div style={{ position: "relative", flex: "0 0 260px" }}>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Tìm tài liệu..."
            aria-label="Tìm kiếm tài liệu"
            style={{ width: "100%", padding: "6px 32px 6px 12px", border: `1px solid ${T.border}`, borderRadius: 6, fontSize: 13, fontFamily: "inherit", color: T.strong, background: T.canvas, outline: "none", minHeight: 36, boxSizing: "border-box" }}
          />
          <span aria-hidden="true" style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", color: T.lightGray }}>⌕</span>
        </div>
        {!isMobile && (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {["all", "Quy trình nội bộ", "Văn bản pháp lý", "Hướng dẫn BRAVO", "Bằng chứng kiểm toán"].map(t => (
              <button key={t} onClick={() => setFilterType(t)} style={{ fontSize: 12, padding: "4px 10px", borderRadius: 6, border: `1px solid ${T.border}`, background: filterType === t ? T.softTeal : T.white, color: filterType === t ? T.interactive : T.secondary, cursor: "pointer", fontFamily: "inherit", minHeight: 36 }}>
                {t === "all" ? "Tất cả" : t}
              </button>
            ))}
          </div>
        )}
        <Button variant="secondary" size="sm" style={{ marginLeft: "auto" }}>+ Tải lên</Button>
      </div>

      {qa.enabled && (
        <div style={{ padding: "4px 20px", borderBottom: `1px solid ${T.border}` }}>
          <IllustrationLabel />
        </div>
      )}

      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        <div style={{ flex: 1, overflowY: "auto", padding: "12px 20px" }}>
          {filtered.length === 0 ? (
            <EmptyState title="Không tìm thấy tài liệu" body="Thử điều chỉnh bộ lọc hoặc từ khóa tìm kiếm." icon="☰" />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {filtered.map(doc => (
                <DocRow key={doc.id} doc={doc} selected={selectedId === doc.id} onClick={() => setSelectedId(selectedId === doc.id ? null : doc.id)} />
              ))}
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selectedDoc && !isMobile && (
          <aside style={{ width: 360, flexShrink: 0, borderLeft: `1px solid ${T.border}`, background: T.white, overflowY: "auto", padding: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: T.strong }}>Chi tiết tài liệu</span>
              <button onClick={() => setSelectedId(null)} aria-label="Đóng chi tiết" style={{ background: "none", border: "none", color: T.secondary, cursor: "pointer", fontSize: 18, minHeight: 36, minWidth: 36, borderRadius: 4 }}>×</button>
            </div>
            <DocDetail doc={selectedDoc} />
          </aside>
        )}
      </div>

      {/* Mobile detail sheet */}
      {selectedDoc && isMobile && (
        <>
          <div onClick={() => setSelectedId(null)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)", zIndex: 30 }} aria-hidden="true" />
          <div role="dialog" aria-modal="true" aria-label="Chi tiết tài liệu" style={{ position: "fixed", inset: 0, top: "auto", height: "75vh", background: T.white, zIndex: 40, borderRadius: "12px 12px 0 0", overflow: "auto", padding: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: T.strong }}>Chi tiết tài liệu</span>
              <button onClick={() => setSelectedId(null)} aria-label="Đóng" style={{ background: "none", border: "none", fontSize: 20, cursor: "pointer", minHeight: 44, minWidth: 44, display: "flex", alignItems: "center", justifyContent: "center" }}>×</button>
            </div>
            <DocDetail doc={selectedDoc} />
          </div>
        </>
      )}
    </div>
  );
}

function DocRow({ doc, selected, onClick }: { doc: KnowledgeDoc; selected: boolean; onClick: () => void }) {
  const tc = TYPE_COLORS[doc.type];
  const al = APPROVAL_LABELS[doc.approvalStatus];
  const il = INGESTION_LABELS[doc.ingestionStatus];
  return (
    <button
      onClick={onClick}
      aria-pressed={selected}
      style={{ width: "100%", textAlign: "left", padding: "14px 16px", background: selected ? T.softTeal : T.white, border: `1px solid ${selected ? T.green : T.border}`, borderRadius: 8, cursor: "pointer", fontFamily: "inherit", transition: "border-color 150ms" }}
      onMouseEnter={e => { if (!selected) (e.currentTarget as HTMLElement).style.borderColor = T.green; }}
      onMouseLeave={e => { if (!selected) (e.currentTarget as HTMLElement).style.borderColor = T.border; }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
        <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 4, background: tc.bg, color: tc.text, fontWeight: 500, whiteSpace: "nowrap", flexShrink: 0, marginTop: 2 }}>{doc.type}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ margin: "0 0 3px", fontSize: 13, fontWeight: 500, color: T.strong, lineHeight: "18px" }}>{doc.name}</p>
          <p style={{ margin: 0, fontSize: 12, color: T.secondary }}>
            {doc.owner} · Hiệu lực: {doc.effectiveDate.known ? doc.effectiveDate.value : "Chưa xác định"}
          </p>
        </div>
        <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
          <span style={{ fontSize: 11, fontWeight: 500, color: al.color, background: al.bg, borderRadius: 4, padding: "1px 6px", whiteSpace: "nowrap" }}>{al.label}</span>
          <span style={{ fontSize: 11, fontWeight: 500, color: il.color, background: il.bg, borderRadius: 4, padding: "1px 6px", whiteSpace: "nowrap" }}>{il.label}</span>
        </div>
      </div>
      {doc.conflictNote && (
        <p style={{ margin: "8px 0 0", fontSize: 12, color: T.error, padding: "6px 10px", background: T.errorSurface, borderRadius: 4 }}>⚠ {doc.conflictNote}</p>
      )}
    </button>
  );
}

function DocDetail({ doc }: { doc: KnowledgeDoc }) {
  const rows = [
    ["Loại tài liệu",    doc.type],
    ["Chủ sở hữu",       doc.owner],
    ["Phiên bản BRAVO",  doc.bravoVersion.known   ? doc.bravoVersion.value   : "Chưa xác định"],
    ["Hiệu lực từ",      doc.effectiveDate.known  ? doc.effectiveDate.value  : "Chưa xác định"],
    ["Phạm vi hiển thị", doc.visibility],
    ["Truy xuất nguồn",  doc.traceability.known   ? doc.traceability.value   : "Chưa xác định"],
  ];
  return (
    <div>
      <h3 style={{ margin: "0 0 14px", fontSize: 14, fontWeight: 600, color: T.strong, lineHeight: "20px" }}>{doc.name}</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {rows.map(([k, v]) => (
          <div key={k}>
            <p style={{ margin: "0 0 2px", fontSize: 11, fontWeight: 600, color: T.secondary, textTransform: "uppercase", letterSpacing: "0.06em" }}>{k}</p>
            <p style={{ margin: 0, fontSize: 13, color: T.strong }}>{v}</p>
          </div>
        ))}
        {doc.supersededBy && (
          <Banner variant="warning">Tài liệu này đã bị thay thế bởi: {doc.supersededBy}</Banner>
        )}
        {doc.supersedes && (
          <p style={{ margin: 0, fontSize: 12, color: T.secondary }}>Thay thế cho: {doc.supersedes}</p>
        )}
        {doc.conflictNote && <Banner variant="error">{doc.conflictNote}</Banner>}
        {doc.ingestionError && <Banner variant="error">Lỗi nạp dữ liệu: {doc.ingestionError}</Banner>}
      </div>
    </div>
  );
}
