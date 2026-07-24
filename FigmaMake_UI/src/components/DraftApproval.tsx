import React, { useState, useRef } from "react";
import { DraftLifecycleBadge, Button, T, Banner, EmptyState, PermissionDeniedState, IllustrationLabel, useFocusTrap } from "./shared";
import { useApp } from "../context/AppContext";
import { ROLE_PERMISSIONS } from "../state/types";
import type { DraftItem } from "../state/types";

export default function DraftApproval() {
  const { state, dispatch } = useApp();
  const perms = ROLE_PERMISSIONS[state.role];
  const [requestChangesDialogOpen, setRequestChangesDialogOpen] = useState(false);
  const [requestChangesNote, setRequestChangesNote] = useState("");
  const [pendingAction, setPendingAction] = useState<{ id: string; action: "request_changes" } | null>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  useFocusTrap(dialogRef, requestChangesDialogOpen);

  const [width, setWidth] = useState(window.innerWidth);
  React.useEffect(() => {
    const h = () => setWidth(window.innerWidth);
    window.addEventListener("resize", h);
    return () => window.removeEventListener("resize", h);
  }, []);
  const isMobile = width < 768;

  if (!perms.canApprove) return <PermissionDeniedState message="Anh/chị không có quyền xem danh sách phê duyệt." />;

  const drafts = state.drafts;
  const selectedId = state.selectedDraftId ?? drafts[0]?.id ?? null;
  const selected = drafts.find(d => d.id === selectedId) ?? null;

  function handleAction(draftId: string, action: "approve" | "reject" | "request_changes", note?: string) {
    if (action === "request_changes" && !note) {
      setPendingAction({ id: draftId, action: "request_changes" });
      setRequestChangesDialogOpen(true);
      return;
    }
    const draft = state.drafts.find(item => item.id === draftId);
    if (!draft) return;
    dispatch({ type: "DRAFT_ACTION", draftId, action, expectedRevision: draft.revision, note });
  }

  function submitRequestChanges() {
    if (!pendingAction || !requestChangesNote.trim()) return;
    const draft = state.drafts.find(item => item.id === pendingAction.id);
    if (!draft) return;
    dispatch({ type: "DRAFT_ACTION", draftId: pendingAction.id, action: "request_changes", expectedRevision: draft.revision, note: requestChangesNote.trim() });
    setRequestChangesDialogOpen(false);
    setRequestChangesNote("");
    setPendingAction(null);
  }

  if (isMobile) {
    return (
      <div style={{ flex: 1, overflowY: "auto" }}>
        {selected
          ? <MobileDetail draft={selected} onBack={() => dispatch({ type: "SELECT_DRAFT", id: null })} onAction={handleAction} canApprove={perms.canApprove} />
          : <MobileQueue drafts={drafts} onSelect={id => dispatch({ type: "SELECT_DRAFT", id })} />
        }
        <RequestChangesDialog open={requestChangesDialogOpen} note={requestChangesNote} onChange={setRequestChangesNote} onSubmit={submitRequestChanges} onClose={() => { setRequestChangesDialogOpen(false); setPendingAction(null); }} dialogRef={dialogRef} />
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
      {/* Queue */}
      <div style={{ width: 300, flexShrink: 0, borderRight: `1px solid ${T.border}`, background: T.white, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "14px 20px", borderBottom: `1px solid ${T.border}` }}>
          <p style={{ margin: 0, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary }}>Hàng chờ phê duyệt</p>
        </div>
        {drafts.length === 0 ? (
          <EmptyState title="Không có bản nháp" body="Không có bản nháp nào đang chờ xem xét." />
        ) : (
          <div style={{ flex: 1, overflowY: "auto", padding: "6px 0" }}>
            {drafts.map(d => (
              <QueueItem key={d.id} draft={d} selected={selectedId === d.id} onClick={() => dispatch({ type: "SELECT_DRAFT", id: d.id })} />
            ))}
          </div>
        )}
      </div>

      {/* Detail */}
      <div style={{ flex: 1, overflowY: "auto", padding: "32px 40px", background: T.canvas }}>
        {selected
          ? <DraftDetail draft={selected} onAction={handleAction} canApprove={perms.canApprove} />
          : <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: T.secondary, fontSize: 14 }}>Chọn một bản nháp để xem chi tiết.</div>
        }
      </div>

      <RequestChangesDialog open={requestChangesDialogOpen} note={requestChangesNote} onChange={setRequestChangesNote} onSubmit={submitRequestChanges} onClose={() => { setRequestChangesDialogOpen(false); setPendingAction(null); }} dialogRef={dialogRef} />
    </div>
  );
}

function QueueItem({ draft, selected, onClick }: { draft: DraftItem; selected: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      aria-current={selected ? "true" : undefined}
      style={{ width: "100%", textAlign: "left", padding: "12px 20px", background: selected ? T.softTeal : "transparent", borderLeft: `3px solid ${selected ? T.green : "transparent"}`, border: "none", cursor: "pointer", fontFamily: "inherit", transition: "background 150ms", minHeight: 44 }}
    >
      <p style={{ margin: "0 0 6px", fontSize: 13, fontWeight: 500, color: T.strong, lineHeight: "18px" }}>{draft.title}</p>
      <DraftLifecycleBadge status={draft.status} />
    </button>
  );
}

function DraftDetail({ draft, onAction, canApprove }: { draft: DraftItem; onAction: (id: string, action: "approve" | "reject" | "request_changes", note?: string) => void; canApprove: boolean }) {
  const actionBlocked = (draft.validationIssues?.length ?? 0) > 0 || draft.missingChecks.length > 0 || draft.status !== "ready_for_review";
  const isTerminal = ["rejected", "approved", "exported_for_manual_action", "externally_executed", "verified"].includes(draft.status);

  return (
    <div style={{ maxWidth: 720 }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 16, marginBottom: 24 }}>
        <div style={{ flex: 1 }}>
          <Banner variant="draft">
            <strong>Bản nháp — chưa được thực hiện trên hệ thống.</strong> Phê duyệt không đồng nghĩa đã ghi vào BRAVO ERP.
          </Banner>
          <h2 style={{ margin: "12px 0 4px", fontSize: 18, fontWeight: 600, color: T.strong, lineHeight: "26px" }}>{draft.title}</h2>
          <p style={{ margin: 0, fontSize: 13, color: T.secondary }}>Người yêu cầu: <strong>{draft.requesterRole}</strong> · Phiên bản {draft.revision}</p>
        </div>
        <DraftLifecycleBadge status={draft.status} />
      </div>

      <InfoCard title="Mục đích thay đổi"><p style={{ margin: 0, fontSize: 14, lineHeight: "22px", color: T.strong }}>{draft.purpose}</p></InfoCard>
      <InfoCard title="Phạm vi ảnh hưởng"><p style={{ margin: 0, fontSize: 14, color: T.strong }}>{draft.scope}</p></InfoCard>

      <InfoCard title="So sánh trước / sau">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <p style={{ margin: "0 0 6px", fontSize: 11, fontWeight: 600, color: T.secondary, textTransform: "uppercase" }}>Trước</p>
            <div style={{ padding: "10px 14px", background: T.canvas, border: `1px solid ${T.border}`, borderRadius: 6, fontSize: 13, color: T.strong }}>{draft.beforeState}</div>
          </div>
          <div>
            <p style={{ margin: "0 0 6px", fontSize: 11, fontWeight: 600, color: T.interactive, textTransform: "uppercase" }}>Sau (đề xuất)</p>
            <div style={{ padding: "10px 14px", background: T.softTeal, border: `1px solid ${T.green}`, borderRadius: 6, fontSize: 13, color: T.strong }}>{draft.afterState}</div>
          </div>
        </div>
      </InfoCard>

      {draft.risk && (
        <Banner variant="warning"><strong>Rủi ro:</strong> {draft.risk}</Banner>
      )}

      {draft.validationIssues && draft.validationIssues.length > 0 && (
        <div style={{ margin: "12px 0" }}>
          <Banner variant="error">
            <strong>Kiểm tra thất bại — Không thể phê duyệt:</strong>
            <ul style={{ margin: "6px 0 0", paddingLeft: 16 }}>
              {draft.validationIssues.map((v, i) => <li key={i}>{v}</li>)}
            </ul>
          </Banner>
        </div>
      )}

      {draft.missingChecks.length > 0 && (
        <InfoCard title="Kiểm tra còn thiếu">
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {draft.missingChecks.map((c, i) => <li key={i} style={{ fontSize: 13, color: T.secondary, marginBottom: 4 }}>{c}</li>)}
          </ul>
        </InfoCard>
      )}

      {draft.changesRequestedNote && (
        <Banner variant="warning"><strong>Ghi chú yêu cầu chỉnh sửa:</strong> {draft.changesRequestedNote}</Banner>
      )}
      {draft.rejectionReason && (
        <Banner variant="error"><strong>Lý do từ chối:</strong> {draft.rejectionReason}</Banner>
      )}

      <InfoCard title="Lịch sử thao tác">
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {draft.auditTrail.map((a, i) => (
            <div key={i} style={{ display: "flex", gap: 12, fontSize: 13, color: T.secondary }}>
              <span style={{ color: T.lightGray, whiteSpace: "nowrap", flexShrink: 0 }}>{a.timestampLabel}</span>
              <span><strong style={{ color: T.strong }}>{a.role}</strong> — {a.event}{a.note ? <span style={{ color: T.lightGray }}> ({a.note})</span> : null}</span>
              <span style={{ marginLeft: "auto", fontSize: 11, color: T.lightGray, flexShrink: 0 }}>Rev {a.revision}</span>
            </div>
          ))}
        </div>
      </InfoCard>

      {/* QA label */}
      <IllustrationLabel />

      {/* Approval note */}
      {draft.status === "approved" && (
        <div style={{ marginTop: 16 }}>
          <Banner variant="success">
            <strong>Đã phê duyệt.</strong> Bản nháp này đã được phê duyệt nhưng <strong>chưa được thực hiện trên BRAVO ERP.</strong> Để ghi vào hệ thống, cần thực hiện thủ công hoặc qua quy trình xuất dữ liệu có kiểm soát.
          </Banner>
        </div>
      )}

      {/* Actions */}
      {canApprove && !isTerminal && (
        <div style={{ display: "flex", gap: 10, marginTop: 20, flexWrap: "wrap" }}>
          {!actionBlocked ? (
            <Button variant="primary" onClick={() => onAction(draft.id, "approve")}>✓ Phê duyệt</Button>
          ) : (
            <Button variant="primary" disabled title="Không thể phê duyệt — cần giải quyết vấn đề kiểm tra trước.">✓ Phê duyệt</Button>
          )}
          <Button variant="secondary" onClick={() => onAction(draft.id, "request_changes")}>↩ Yêu cầu chỉnh sửa</Button>
          <Button variant="danger" onClick={() => onAction(draft.id, "reject", "Bản nháp bị từ chối vì chưa đáp ứng điều kiện xem xét.")}>✕ Từ chối</Button>
        </div>
      )}
      {!canApprove && !isTerminal && (
        <Banner variant="warning">Anh/chị không có quyền phê duyệt bản nháp này.</Banner>
      )}
    </div>
  );
}

function MobileQueue({ drafts, onSelect }: { drafts: DraftItem[]; onSelect: (id: string) => void }) {
  return (
    <div>
      <div style={{ padding: "14px 16px", borderBottom: `1px solid ${T.border}`, background: T.white }}>
        <p style={{ margin: 0, fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary }}>Hàng chờ phê duyệt</p>
      </div>
      {drafts.map(d => (
        <button key={d.id} onClick={() => onSelect(d.id)} style={{ width: "100%", textAlign: "left", padding: "14px 16px", background: T.white, border: "none", borderBottom: `1px solid ${T.border}`, cursor: "pointer", fontFamily: "inherit", minHeight: 44 }}>
          <p style={{ margin: "0 0 6px", fontSize: 13, fontWeight: 500, color: T.strong }}>{d.title}</p>
          <DraftLifecycleBadge status={d.status} />
        </button>
      ))}
    </div>
  );
}

function MobileDetail({ draft, onBack, onAction, canApprove }: { draft: DraftItem; onBack: () => void; onAction: any; canApprove: boolean }) {
  return (
    <div>
      <div style={{ padding: "12px 16px", background: T.white, borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", gap: 12 }}>
        <button onClick={onBack} style={{ background: "none", border: "none", color: T.interactive, cursor: "pointer", fontSize: 14, fontFamily: "inherit", minHeight: 44, padding: "0 8px" }}>← Quay lại</button>
        <DraftLifecycleBadge status={draft.status} />
      </div>
      <div style={{ padding: "20px 16px" }}>
        <DraftDetail draft={draft} onAction={onAction} canApprove={canApprove} />
      </div>
    </div>
  );
}

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <p style={{ margin: "0 0 6px", fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary }}>{title}</p>
      <div style={{ padding: "12px 16px", background: T.white, border: `1px solid ${T.border}`, borderRadius: 8 }}>{children}</div>
    </div>
  );
}

function RequestChangesDialog({ open, note, onChange, onSubmit, onClose, dialogRef }: {
  open: boolean; note: string; onChange: (v: string) => void;
  onSubmit: () => void; onClose: () => void;
  dialogRef: React.RefObject<HTMLDivElement | null>;
}) {
  if (!open) return null;
  return (
    <>
      <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", zIndex: 50 }} aria-hidden="true" />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="rc-dialog-title"
        style={{ position: "fixed", top: "50%", left: "50%", transform: "translate(-50%,-50%)", background: T.white, borderRadius: 10, padding: 28, width: "min(480px, 90vw)", zIndex: 51, boxShadow: "0 8px 32px rgba(0,0,0,0.18)" }}
      >
        <h2 id="rc-dialog-title" style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600, color: T.strong }}>Yêu cầu chỉnh sửa</h2>
        <p style={{ margin: "0 0 16px", fontSize: 14, color: T.secondary }}>Ghi rõ điều cần chỉnh sửa. Ghi chú này bắt buộc và sẽ được lưu vào lịch sử.</p>
        <textarea
          value={note}
          onChange={e => onChange(e.target.value)}
          placeholder="Mô tả điều cần chỉnh sửa..."
          rows={4}
          autoFocus
          style={{ width: "100%", padding: "8px 12px", border: `1px solid ${T.border}`, borderRadius: 6, fontSize: 14, fontFamily: "inherit", resize: "vertical", boxSizing: "border-box" }}
        />
        <div style={{ display: "flex", gap: 10, marginTop: 16, justifyContent: "flex-end" }}>
          <Button variant="ghost" onClick={onClose}>Hủy</Button>
          <Button variant="primary" onClick={onSubmit} disabled={!note.trim()}>Gửi yêu cầu chỉnh sửa</Button>
        </div>
      </div>
    </>
  );
}
