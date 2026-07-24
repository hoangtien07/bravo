import React, { useState } from "react";
import { DiagonalMotif, StatusBadge, Button, T, EmptyState, PermissionDeniedState, SkeletonBlock, Banner, prereqStatusToEvidenceStatus, IllustrationLabel } from "./shared";
import { useApp } from "../context/AppContext";
import { useQA } from "../context/QAContext";
import { ROLE_PERMISSIONS } from "../state/types";
import type { PrerequisiteNode } from "../state/types";
import { useNavigate } from "react-router-dom";
export default function FinancialCloseReadiness() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const onNavigate = (s: any) => { dispatch({ type: "NAVIGATE", screen: s }); if (s === "financial-graph") navigate("/financial-close/graph"); };
  const { qa } = useQA();
  const perms = ROLE_PERMISSIONS[state.role];
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [width, setWidth] = useState(window.innerWidth);
  React.useEffect(() => {
    const h = () => setWidth(window.innerWidth);
    window.addEventListener("resize", h);
    return () => window.removeEventListener("resize", h);
  }, []);
  const isMobile = width < 768;

  // Permission boundary
  if (!perms.canViewGraph && !perms.canViewKnowledge) {
    return <PermissionDeniedState />;
  }

  // Loading state
  if (qa.componentState === "loading") {
    return (
      <div style={{ flex: 1, padding: 32 }}>
        <SkeletonBlock />
      </div>
    );
  }

  // Empty (no scope set)
  if (qa.componentState === "empty" || (state.scope.accountingPeriod.known === false && qa.scenario === "default_unknown" && state.prerequisites.every(p => p.status === "not_assessed"))) {
    if (qa.componentState === "empty") {
      return (
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <EmptyState
            title="Chưa có phạm vi đóng kỳ"
            body="Chọn công ty và kỳ kế toán trong ngữ cảnh để bắt đầu đánh giá điều kiện đóng kỳ."
            icon="⊟"
            action={<Button variant="secondary" size="sm" onClick={() => onNavigate?.("new-conversation")}>Bắt đầu từ hội thoại mới</Button>}
          />
        </div>
      );
    }
  }

  const nodes = state.prerequisites;
  const selectedNode = nodes.find(n => n.id === selectedId);

  const counts = {
    ready:    nodes.filter(n => n.status === "ready").length,
    progress: nodes.filter(n => n.status === "in_progress").length,
    missing:  nodes.filter(n => n.status === "missing_evidence").length,
    conflict: nodes.filter(n => n.status === "conflict").length,
    blocked:  nodes.filter(n => n.status === "blocked").length,
    notDone:  nodes.filter(n => n.status === "not_assessed").length,
  };

  if (isMobile) {
    return (
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        <MobileSummary counts={counts} />
        <Button variant="ghost" size="sm" onClick={() => onNavigate("financial-graph")} style={{ marginTop: 10, width: "100%", justifyContent: "center" }}>
          Xem sơ đồ bằng chứng →
        </Button>
        <div style={{ marginTop: 16 }}>
          {nodes.map((node, idx) => (
            <MobileNodeRow key={node.id} node={node} isLast={idx === nodes.length - 1} />
          ))}
        </div>
        {qa.enabled && <div style={{ marginTop: 16 }}><IllustrationLabel /></div>}
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
      {/* Rail panel */}
      <div style={{ width: 420, flexShrink: 0, borderRight: `1px solid ${T.border}`, background: T.white, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "18px 24px", borderBottom: `1px solid ${T.border}` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
            <DiagonalMotif size={16} color={T.green} />
            <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: T.strong }}>Sẵn sàng đóng kỳ</h2>
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
            <SummaryChip label="Sẵn sàng"    count={counts.ready}    color={T.interactive} bg={T.softTeal} />
            <SummaryChip label="Đang xử lý"  count={counts.progress} color={T.interactive} bg={T.softTeal} />
            <SummaryChip label="Thiếu"        count={counts.missing}  color={T.warningText} bg={T.warnSurface} />
            <SummaryChip label="Xung đột"     count={counts.conflict} color={T.error}      bg={T.errorSurface} />
            {counts.blocked > 0 && <SummaryChip label="Bị chặn"  count={counts.blocked} color={T.error}   bg={T.errorSurface} />}
            <SummaryChip label="Chưa đánh giá" count={counts.notDone} color={T.secondary} bg={T.canvas} />
          </div>
          {!state.scope.accountingPeriod.known && (
            <Banner variant="warning">Phạm vi kỳ kế toán chưa được xác định. Các điều kiện hiển thị là mặc định chưa đánh giá.</Banner>
          )}
          <button onClick={() => onNavigate("financial-graph")} style={{ marginTop: 8, fontSize: 12, color: T.interactive, background: "none", border: "none", cursor: "pointer", padding: 0, fontFamily: "inherit", display: "flex", alignItems: "center", gap: 4 }}>
            Xem sơ đồ bằng chứng →
          </button>
          {qa.enabled && <div style={{ marginTop: 8 }}><IllustrationLabel /></div>}
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "12px 0" }}>
          {nodes.map((node, idx) => (
            <RailNode
              key={node.id}
              node={node}
              isLast={idx === nodes.length - 1}
              selected={selectedId === node.id}
              onSelect={() => setSelectedId(selectedId === node.id ? null : node.id)}
            />
          ))}
        </div>
      </div>

      {/* Detail panel */}
      <div style={{ flex: 1, overflowY: "auto", padding: "32px 40px", background: T.canvas }}>
        {selectedNode
          ? <DetailPanel node={selectedNode} evidence={state.evidence.filter(e => selectedNode.evidenceRefs.includes(e.id))} />
          : (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 16, color: T.secondary }}>
              <DiagonalMotif size={48} color={T.border} />
              <p style={{ fontSize: 14 }}>Chọn một bước để xem chi tiết bằng chứng và điều kiện.</p>
            </div>
          )
        }
      </div>
    </div>
  );
}

function SummaryChip({ label, count, color, bg }: { label: string; count: number; color: string; bg: string }) {
  return (
    <span style={{ fontSize: 12, fontWeight: 500, color, background: bg, borderRadius: 4, padding: "2px 8px", display: "inline-flex", gap: 4 }}>
      <span style={{ fontWeight: 700 }}>{count}</span> {label}
    </span>
  );
}

function RailNode({ node, isLast, selected, onSelect }: { node: PrerequisiteNode; isLast: boolean; selected: boolean; onSelect: () => void }) {
  const motifColor = node.status === "ready" ? T.green : node.status === "conflict" || node.status === "blocked" ? T.error : node.status === "missing_evidence" ? T.orange : T.border;
  const badgeStatus = prereqStatusToEvidenceStatus(node.status);
  return (
    <div style={{ display: "flex", paddingLeft: 20 }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 32, flexShrink: 0 }}>
        <div style={{ width: 2, height: 12, background: T.border }} />
        <DiagonalMotif size={15} color={motifColor} />
        {!isLast && <div style={{ flex: 1, width: 2, background: T.border, marginTop: 4 }} />}
      </div>
      <button
        onClick={onSelect}
        aria-current={selected ? "true" : undefined}
        style={{ flex: 1, textAlign: "left", padding: "8px 16px 14px 10px", background: selected ? T.softTeal : "transparent", border: "none", borderLeft: `2px solid ${selected ? T.green : "transparent"}`, cursor: "pointer", fontFamily: "inherit", transition: "background 150ms", minHeight: 44 }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
          <div>
            <span style={{ fontSize: 10, color: T.lightGray, fontWeight: 500 }}>Bước {node.step}</span>
            <p style={{ margin: "2px 0 4px", fontSize: 13, fontWeight: 600, color: T.strong, lineHeight: "18px" }}>{node.title}</p>
          </div>
          <StatusBadge status={badgeStatus} compact />
        </div>
        {selected && <p style={{ margin: 0, fontSize: 12, color: T.secondary, lineHeight: "18px" }}>{node.reason}</p>}
      </button>
    </div>
  );
}

function DetailPanel({ node, evidence }: { node: PrerequisiteNode; evidence: ReturnType<typeof useApp>["state"]["evidence"] }) {
  const badgeStatus = prereqStatusToEvidenceStatus(node.status);
  return (
    <div style={{ maxWidth: 680 }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, marginBottom: 24 }}>
        <div>
          <span style={{ fontSize: 12, color: T.lightGray, fontWeight: 500 }}>Bước {node.step} / 8</span>
          <h2 style={{ margin: "4px 0 8px", fontSize: 20, lineHeight: "28px", fontWeight: 600, color: T.strong }}>{node.title}</h2>
          <p style={{ margin: 0, fontSize: 14, color: T.secondary, lineHeight: "22px" }}>{node.description}</p>
        </div>
        <StatusBadge status={badgeStatus} />
      </div>

      <InfoCard title="Lý do đánh giá">
        <p style={{ margin: 0, fontSize: 14, color: T.strong, lineHeight: "22px" }}>{node.reason}</p>
      </InfoCard>

      {node.missingEvidence.length > 0 && (
        <InfoCard title="Bằng chứng còn thiếu">
          <ul style={{ margin: 0, paddingLeft: 20, display: "flex", flexDirection: "column", gap: 4 }}>
            {node.missingEvidence.map((m, i) => <li key={i} style={{ fontSize: 13, color: T.error }}>{m}</li>)}
          </ul>
        </InfoCard>
      )}

      <InfoCard title="Bằng chứng hiện có">
        {evidence.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {evidence.map(ev => (
              <div key={ev.id} style={{ padding: "8px 12px", background: T.canvas, border: `1px solid ${T.border}`, borderRadius: 6, fontSize: 13, color: T.strong }}>
                <strong>{ev.claim}</strong>
                <span style={{ marginLeft: 8, fontSize: 12, color: T.secondary }}>{ev.sourceName ?? "Nguồn chưa liên kết"}</span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ margin: 0, fontSize: 13, color: T.lightGray, fontStyle: "italic" }}>Chưa có bằng chứng được liên kết.</p>
        )}
      </InfoCard>

      {node.responsibleRole && (
        <InfoCard title="Người phụ trách">
          <span style={{ fontSize: 14, color: T.strong, fontWeight: 500 }}>{node.responsibleRole}</span>
        </InfoCard>
      )}

      {node.nextSafeAction && (
        <div style={{ padding: "14px 18px", background: T.warnSurface, border: `1px solid ${T.orange}`, borderRadius: 8, marginTop: 4 }}>
          <p style={{ margin: "0 0 4px", fontSize: 11, fontWeight: 600, color: "#92400E", textTransform: "uppercase", letterSpacing: "0.06em" }}>Hành động tiếp theo</p>
          <p style={{ margin: "0 0 12px", fontSize: 14, color: T.strong, lineHeight: "22px" }}>{node.nextSafeAction}</p>
          <Button variant="secondary" size="sm">Tạo yêu cầu bổ sung bằng chứng</Button>
        </div>
      )}

      {node.status === "conflict" && (
        <Banner variant="error">
          Xung đột bằng chứng được phát hiện. Cần giải trình trước khi tiếp tục.
        </Banner>
      )}
      {node.status === "blocked" && (
        <Banner variant="warning">
          Bước này bị chặn bởi điều kiện tiên quyết chưa hoàn thành ở bước trước.
        </Banner>
      )}
    </div>
  );
}

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <p style={{ margin: "0 0 8px", fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary }}>{title}</p>
      <div style={{ padding: "12px 16px", background: "#fff", border: `1px solid ${T.border}`, borderRadius: 8 }}>{children}</div>
    </div>
  );
}

function MobileSummary({ counts }: { counts: Record<string, number> }) {
  return (
    <div style={{ padding: "14px 16px", background: T.white, border: `1px solid ${T.border}`, borderRadius: 8, marginBottom: 8 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <DiagonalMotif size={14} color={T.green} />
        <h2 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: T.strong }}>Sẵn sàng đóng kỳ</h2>
      </div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        <SummaryChip label="Sẵn sàng"     count={counts.ready}    color={T.interactive} bg={T.softTeal} />
        <SummaryChip label="Thiếu"         count={counts.missing}  color={T.warningText} bg={T.warnSurface} />
        <SummaryChip label="Xung đột"      count={counts.conflict} color={T.error}       bg={T.errorSurface} />
        <SummaryChip label="Chưa đánh giá" count={counts.notDone}  color={T.secondary}  bg={T.canvas} />
      </div>
    </div>
  );
}

function MobileNodeRow({ node, isLast }: { node: PrerequisiteNode; isLast: boolean }) {
  const [open, setOpen] = useState(false);
  const badgeStatus = prereqStatusToEvidenceStatus(node.status);
  return (
    <div style={{ borderBottom: isLast ? "none" : `1px solid ${T.border}` }}>
      <button onClick={() => setOpen(v => !v)} style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 4px", background: "none", border: "none", cursor: "pointer", fontFamily: "inherit", gap: 8, minHeight: 44 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, minWidth: 0 }}>
          <span style={{ fontSize: 11, color: T.lightGray, flexShrink: 0 }}>{node.step}</span>
          <span style={{ fontSize: 13, fontWeight: 500, color: T.strong, textAlign: "left" }}>{node.title}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          <StatusBadge status={badgeStatus} compact />
          <span style={{ color: T.secondary, fontSize: 12 }}>{open ? "▲" : "▼"}</span>
        </div>
      </button>
      {open && (
        <div style={{ padding: "8px 4px 16px", fontSize: 13, color: T.secondary, lineHeight: "20px" }}>
          <p style={{ margin: "0 0 6px" }}>{node.reason}</p>
          {node.nextSafeAction && <p style={{ margin: "0 0 6px", color: "#92400E", fontWeight: 500 }}>↳ {node.nextSafeAction}</p>}
          {node.responsibleRole && <p style={{ margin: 0, color: T.lightGray, fontSize: 12 }}>Phụ trách: {node.responsibleRole}</p>}
        </div>
      )}
    </div>
  );
}
