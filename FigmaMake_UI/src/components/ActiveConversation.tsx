import React, { useState, useEffect, useRef } from "react";
import { DiagonalMotif, StatusBadge, Button, T, Banner, EmptyState, EvidenceClassBadge } from "./shared";
import { useApp } from "../context/AppContext";
import type { EvidenceRef } from "../state/types";
import { fixtureId } from "../fixtures/runtime";

type LocalMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  evidenceRefs: string[];
  isStreaming?: boolean;
};

export default function ActiveConversation() {
  const { state, dispatch } = useApp();
  const task = state.task;

  const [messages, setMessages] = useState<LocalMessage[]>(() => buildInitialMessages(state.conversationPrompt));
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(messages.some(m => m.isStreaming));
  const [showEvidence, setShowEvidence] = useState(true);
  const [mobileEvidenceOpen, setMobileEvidenceOpen] = useState(false);
  const [attachments, setAttachments] = useState<string[]>([]);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const activeRunRef = useRef(0);

  // Track width for responsive
  const [width, setWidth] = useState(window.innerWidth);
  useEffect(() => {
    const h = () => setWidth(window.innerWidth);
    window.addEventListener("resize", h);
    return () => window.removeEventListener("resize", h);
  }, []);
  const isMobile = width < 768;

  useEffect(() => {
    // Simulate streaming the first assistant response
    const streaming = messages.find(m => m.isStreaming);
    if (!streaming) return;
    const full = getAssistantReply(state.conversationPrompt);
    const run = ++activeRunRef.current;
    let i = 0;
    const interval = setInterval(() => {
      if (activeRunRef.current !== run) { clearInterval(interval); return; }
      i += 5;
      setMessages(prev => prev.map(m => m.id === streaming.id ? { ...m, content: full.slice(0, i) } : m));
      if (i >= full.length) {
        clearInterval(interval);
        setMessages(prev => prev.map(m => m.id === streaming.id ? { ...m, content: full, isStreaming: false } : m));
        setIsStreaming(false);
      }
    }, 20);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  function sendMessage() {
    const text = input.trim();
    if (!text || isStreaming) return;
    const userMsg: LocalMessage = { id: fixtureId("message:user"), role: "user", content: text, evidenceRefs: [] };
    const assistantId = fixtureId("message:assistant");
    const assistantMsg: LocalMessage = { id: assistantId, role: "assistant", content: "", evidenceRefs: ["ev-1", "ev-3"], isStreaming: true };
    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setInput("");
    setAttachments([]);
    setIsStreaming(true);

    const reply = getFollowUpReply();
    let i = 0;
    const run = ++activeRunRef.current;
    const interval = setInterval(() => {
      if (activeRunRef.current !== run) { clearInterval(interval); return; }
      i += 5;
      setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: reply.slice(0, i) } : m));
      if (i >= reply.length) {
        clearInterval(interval);
        setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: reply, isStreaming: false } : m));
        setIsStreaming(false);
      }
    }, 20);
  }

  function stopStreaming() {
    activeRunRef.current += 1;
    setMessages(current => current.map(message => message.isStreaming ? { ...message, isStreaming: false, content: `${message.content}\n\n[Đã dừng — nội dung chưa hoàn chỉnh]` } : message));
    setIsStreaming(false);
  }

  return (
    <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
      {/* History sidebar — hidden on mobile */}
      {!isMobile && (
        <div style={{ width: 220, flexShrink: 0, borderRight: `1px solid ${T.border}`, background: T.white, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", borderBottom: `1px solid ${T.border}` }}>
            <p style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: T.secondary, margin: 0 }}>Lịch sử</p>
          </div>
          <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
            <div style={{ padding: "8px 16px", background: T.softTeal, borderLeft: `3px solid ${T.green}` }}>
              <p style={{ margin: 0, fontSize: 12, color: T.interactive, fontWeight: 500, lineHeight: "18px" }}>
                {task?.outcome ?? "Hội thoại hiện tại"}
              </p>
              {task && (
                <span style={{ fontSize: 10, color: T.lightGray, marginTop: 2, display: "block" }}>
                  {task.status === "active" ? "Đang hoạt động" : task.status === "paused" ? "Tạm dừng" : task.status === "cancelled" ? "Đã hủy" : "Hoàn tất"}
                </span>
              )}
            </div>
            <div style={{ padding: "6px 16px" }}>
              <p style={{ margin: 0, fontSize: 11, color: T.lightGray, fontStyle: "italic" }}>Các hội thoại cũ sẽ xuất hiện ở đây.</p>
            </div>
          </div>
          {/* Task controls */}
          {task && task.status === "active" && (
            <div style={{ padding: "8px 12px", borderTop: `1px solid ${T.border}`, display: "flex", gap: 6 }}>
              <Button variant="ghost" size="sm" onClick={() => dispatch({ type: "PAUSE_TASK" })} style={{ flex: 1, justifyContent: "center", fontSize: 11 }}>⏸ Tạm dừng</Button>
              <Button variant="ghost" size="sm" onClick={() => dispatch({ type: "CANCEL_TASK" })} style={{ flex: 1, justifyContent: "center", fontSize: 11, color: T.error }}>✕ Hủy</Button>
            </div>
          )}
          {task && task.status === "paused" && (
            <div style={{ padding: "8px 12px", borderTop: `1px solid ${T.border}` }}>
              <Button variant="secondary" size="sm" onClick={() => dispatch({ type: "RESUME_TASK" })} style={{ width: "100%", justifyContent: "center" }}>▶ Tiếp tục</Button>
            </div>
          )}
        </div>
      )}

      {/* Center conversation */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
        {/* Task status banner */}
        {task && task.status === "cancelled" && (
          <Banner variant="warning">
            Hội thoại này đã bị hủy. Lịch sử vẫn được giữ lại. Bắt đầu cuộc hội thoại mới để tiếp tục.
          </Banner>
        )}
        {task && task.status === "paused" && (
          <Banner variant="info">
            Hội thoại đang tạm dừng. Nhấn <strong>Tiếp tục</strong> trong thanh bên để tiếp tục làm việc.
          </Banner>
        )}

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: isMobile ? "16px" : "24px" }}>
          <div style={{ maxWidth: 760, margin: "0 auto", display: "flex", flexDirection: "column", gap: 24 }}>
            {messages.map(msg => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                evidence={state.evidence}
                selectedEvidenceId={state.selectedEvidenceId}
                onSelectEvidence={id => { dispatch({ type: "SELECT_EVIDENCE", id }); if (isMobile) setMobileEvidenceOpen(true); if (!isMobile) setShowEvidence(true); }}
              />
            ))}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Composer */}
        {(!task || task.status === "active" || task.status === "scoping") && (
          <div style={{ borderTop: `1px solid ${T.border}`, background: T.white, padding: isMobile ? "10px 16px" : "12px 24px" }}>
            <div style={{ maxWidth: 760, margin: "0 auto" }}>
              <div style={{ border: `1px solid ${T.border}`, borderRadius: 8, padding: "10px 14px", background: T.white }}>
                {attachments.length > 0 && <div aria-label="Tệp đính kèm đang chờ" style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 8 }}>{attachments.map(name => <span key={name} style={{ border: `1px solid ${T.border}`, borderRadius: 4, padding: "3px 8px", color: T.secondary, fontSize: 12 }}>{name} · Chờ xử lý <button aria-label={`Xóa ${name}`} onClick={() => setAttachments(current => current.filter(item => item !== name))} style={{ border: 0, background: "transparent", color: T.error, cursor: "pointer" }}>×</button></span>)}</div>}
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                  placeholder="Nhập câu hỏi tiếp theo..."
                  rows={2}
                  aria-label="Soạn câu hỏi tiếp theo"
                  aria-live="polite"
                  style={{ width: "100%", resize: "none", border: "none", outline: "none", fontSize: 14, lineHeight: "22px", color: T.strong, fontFamily: "inherit", background: "transparent" }}
                />
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 6, gap: 8 }}>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input ref={fileRef} type="file" multiple hidden onChange={event => setAttachments(Array.from(event.target.files ?? []).map(file => file.name))} />
                    <button onClick={() => fileRef.current?.click()} aria-label="Đính kèm tệp" style={{ background: "none", border: `1px solid ${T.border}`, borderRadius: 6, padding: "3px 10px", fontSize: 12, color: T.secondary, cursor: "pointer", fontFamily: "inherit", minHeight: 44, minWidth: 44 }}>📎</button>
                    {isStreaming && (
                      <Button variant="danger" size="sm" onClick={stopStreaming} aria-label="Dừng tạo phản hồi">⏹ Dừng</Button>
                    )}
                  </div>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    {!isMobile && (
                      <button
                        onClick={() => setShowEvidence(v => !v)}
                        style={{ fontSize: 12, background: showEvidence ? T.softTeal : "transparent", border: `1px solid ${T.border}`, borderRadius: 6, padding: "3px 10px", color: showEvidence ? T.interactive : T.secondary, cursor: "pointer", fontFamily: "inherit", minHeight: 36 }}
                        aria-pressed={showEvidence}
                      >
                        {showEvidence ? "Ẩn bằng chứng" : "Xem bằng chứng"}
                      </button>
                    )}
                    {isMobile && (
                      <button onClick={() => setMobileEvidenceOpen(true)} style={{ fontSize: 12, background: T.softTeal, border: `1px solid ${T.border}`, borderRadius: 6, padding: "3px 10px", color: T.interactive, cursor: "pointer", fontFamily: "inherit", minHeight: 36 }}>Bằng chứng</button>
                    )}
                    <Button variant="primary" size="sm" onClick={sendMessage} disabled={!input.trim() || isStreaming}>Gửi →</Button>
                  </div>
                </div>
              </div>
              <p style={{ fontSize: 11, color: T.lightGray, marginTop: 4, textAlign: "center" }}>
                Đây là bản nháp. Chưa được thực hiện trên hệ thống.
              </p>
            </div>
          </div>
        )}
        {task?.status === "cancelled" && (
          <div style={{ padding: "12px 24px", borderTop: `1px solid ${T.border}`, background: T.white, textAlign: "center" }}>
            <p style={{ margin: "0 0 8px", fontSize: 13, color: T.secondary }}>Hội thoại đã bị hủy. Composer không khả dụng.</p>
          </div>
        )}
      </div>

      {/* Desktop evidence drawer */}
      {!isMobile && showEvidence && (
        <EvidenceDrawer
          evidence={state.evidence}
          selectedId={state.selectedEvidenceId}
          onSelect={id => dispatch({ type: "SELECT_EVIDENCE", id })}
          onClose={() => setShowEvidence(false)}
        />
      )}

      {/* Mobile evidence sheet */}
      {isMobile && mobileEvidenceOpen && (
        <>
          <div onClick={() => setMobileEvidenceOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)", zIndex: 30 }} aria-hidden="true" />
          <div role="dialog" aria-modal="true" aria-label="Bằng chứng" style={{ position: "fixed", inset: 0, top: "auto", height: "80vh", background: T.white, zIndex: 40, borderRadius: "12px 12px 0 0", display: "flex", flexDirection: "column", boxShadow: "0 -4px 24px rgba(0,0,0,0.15)" }}>
            <div style={{ padding: "16px 20px", borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: T.strong }}>Bằng chứng</span>
              <button onClick={() => setMobileEvidenceOpen(false)} style={{ background: "none", border: "none", color: T.secondary, cursor: "pointer", fontSize: 20, padding: 4, minHeight: 44, minWidth: 44, display: "flex", alignItems: "center", justifyContent: "center" }} aria-label="Đóng ngăn bằng chứng">×</button>
            </div>
            <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px" }}>
              <EvidenceList evidence={state.evidence} selectedId={state.selectedEvidenceId} onSelect={id => dispatch({ type: "SELECT_EVIDENCE", id })} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function MessageBubble({ msg, evidence, selectedEvidenceId, onSelectEvidence }: {
  msg: LocalMessage;
  evidence: EvidenceRef[];
  selectedEvidenceId: string | null;
  onSelectEvidence: (id: string) => void;
}) {
  const [localContent, setLocalContent] = useState(msg.content);
  const [editing, setEditing] = useState(false);
  const [actionStatus, setActionStatus] = useState("");
  if (msg.role === "user") {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <div style={{ maxWidth: "75%", background: T.interactive, color: "white", borderRadius: "12px 12px 4px 12px", padding: "10px 16px", fontSize: 14, lineHeight: "22px" }}>
          {editing ? <><textarea aria-label="Chỉnh sửa tin nhắn" value={localContent} onChange={event => setLocalContent(event.target.value)} style={{ width: "100%", minWidth: 240, color: T.strong, background: T.white, borderRadius: 4, padding: 8 }} /><div style={{ marginTop: 6 }}><button onClick={() => { setEditing(false); setActionStatus("Đã mô phỏng cắt các lượt sau và tăng task revision."); }} style={{ minHeight: 36 }}>Lưu chỉnh sửa</button> <button onClick={() => setEditing(false)} style={{ minHeight: 36 }}>Hủy</button></div></> : localContent}
          {!editing && <button onClick={() => setEditing(true)} style={{ display: "block", marginTop: 6, border: 0, background: "transparent", color: "white", textDecoration: "underline", cursor: "pointer" }}>Chỉnh sửa</button>}
          {actionStatus && <small role="status" style={{ display: "block", marginTop: 4 }}>{actionStatus}</small>}
        </div>
      </div>
    );
  }

  const refList = evidence.filter(e => msg.evidenceRefs.includes(e.id));

  return (
    <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
      {/* Avatar */}
      <div style={{ width: 32, height: 32, flexShrink: 0, background: T.softTeal, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", marginTop: 2 }}>
        <DiagonalMotif size={13} color={T.interactive} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: T.interactive }}>Bravo Agent AI</span>
          <StatusBadge status="draft" compact />
          {msg.isStreaming && <span style={{ fontSize: 11, color: T.secondary, fontStyle: "italic" }}>Đang đối chiếu điều kiện và bằng chứng...</span>}
        </div>
        <div
          style={{ fontSize: 14, lineHeight: "22px", color: T.strong, whiteSpace: "pre-wrap" }}
          aria-live={msg.isStreaming ? "polite" : undefined}
          aria-atomic="false"
        >
          {renderContent(msg.content)}
          {msg.isStreaming && (
            <span aria-hidden="true" style={{ display: "inline-block", width: 8, height: 16, background: T.green, marginLeft: 2, animation: "blink 1s infinite", verticalAlign: "text-bottom" }} />
          )}
        </div>
        {/* Citations */}
        {refList.length > 0 && !msg.isStreaming && (
          <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 6 }}>
            {refList.map(ev => (
              <button
                key={ev.id}
                onClick={() => onSelectEvidence(ev.id)}
                aria-pressed={selectedEvidenceId === ev.id}
                style={{
                  fontSize: 12, padding: "3px 8px", borderRadius: 4, cursor: "pointer",
                  border: `1px solid ${evidenceColor(ev.evidenceClass).border}`,
                  background: evidenceColor(ev.evidenceClass).bg,
                  color: evidenceColor(ev.evidenceClass).text,
                  fontFamily: "inherit",
                }}
              >
                {ev.sourceName ?? ev.id} · {ev.evidenceClass === "missing" ? "Thiếu" : ev.evidenceClass === "conflicting" ? "Xung đột" : ev.evidenceClass === "verified" ? "Đã xác minh" : "Nguồn"}
              </button>
            ))}
          </div>
        )}
        {!msg.isStreaming && <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 6 }}>
          <button onClick={() => setActionStatus("Đã ghi nhận phản hồi hữu ích trong audit fixture.")} style={messageActionStyle}>Hữu ích</button>
          <button onClick={() => setActionStatus("Đã mở lý do báo cáo trong fixture; chưa gửi dữ liệu.")} style={messageActionStyle}>Báo cáo</button>
          <button onClick={() => setActionStatus("Đã tạo preview liên kết chỉ đọc fixture; token không được hiển thị.")} style={messageActionStyle}>Mô phỏng chia sẻ</button>
          <button onClick={() => setActionStatus("Đã mô phỏng tạo lại; sự kiện của run cũ sẽ bị bỏ qua.")} style={messageActionStyle}>Tạo lại</button>
          {actionStatus && <span role="status" style={{ width: "100%", color: T.secondary, fontSize: 12 }}>{actionStatus}</span>}
        </div>}
      </div>
    </div>
  );
}

const messageActionStyle: React.CSSProperties = { minHeight: 36, padding: "4px 9px", border: `1px solid ${T.border}`, borderRadius: 6, background: T.white, color: T.secondary, cursor: "pointer" };

function EvidenceDrawer({ evidence, selectedId, onSelect, onClose }: { evidence: EvidenceRef[]; selectedId: string | null; onSelect: (id: string | null) => void; onClose: () => void; }) {
  return (
    <aside style={{ width: 380, flexShrink: 0, borderLeft: `1px solid ${T.border}`, background: T.white, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ padding: "14px 20px", borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <DiagonalMotif size={14} color={T.green} />
          <span style={{ fontSize: 14, fontWeight: 600, color: T.strong }}>Bằng chứng</span>
        </div>
        <button onClick={onClose} aria-label="Đóng ngăn bằng chứng" style={{ background: "none", border: "none", color: T.secondary, cursor: "pointer", padding: 4, fontSize: 16, minHeight: 36, minWidth: 36, borderRadius: 4 }}>×</button>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px" }}>
        <EvidenceList evidence={evidence} selectedId={selectedId} onSelect={onSelect} />
      </div>
    </aside>
  );
}

function EvidenceList({ evidence, selectedId, onSelect }: { evidence: EvidenceRef[]; selectedId: string | null; onSelect: (id: string | null) => void; }) {
  if (evidence.length === 0) {
    return <EmptyState title="Chưa có bằng chứng" body="Chưa có bằng chứng nào được liên kết với hội thoại này." icon="○" />;
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {evidence.map(ev => (
        <EvidenceCard key={ev.id} item={ev} selected={selectedId === ev.id} onClick={() => onSelect(selectedId === ev.id ? null : ev.id)} />
      ))}
    </div>
  );
}

function EvidenceCard({ item, selected, onClick }: { item: EvidenceRef; selected: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      aria-pressed={selected}
      style={{ border: `1px solid ${selected ? T.green : T.border}`, borderRadius: 8, padding: "12px 14px", background: selected ? T.softTeal : T.white, cursor: "pointer", transition: "border-color 150ms, background 150ms", textAlign: "left", fontFamily: "inherit", width: "100%" }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8, marginBottom: 8 }}>
        <p style={{ margin: 0, fontSize: 13, fontWeight: 500, color: T.strong, lineHeight: "18px" }}>{item.claim}</p>
        <EvidenceClassBadge cls={item.evidenceClass} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "3px 10px", fontSize: 12, color: T.secondary }}>
        <span style={{ color: T.lightGray }}>Nguồn:</span><span>{item.sourceName ?? "Chưa liên kết"}</span>
        {item.locator && <><span style={{ color: T.lightGray }}>Phạm vi:</span><span>{item.locator}</span></>}
        {item.period && <><span style={{ color: T.lightGray }}>Kỳ:</span><span>{item.period}</span></>}
        {item.effectiveStatus && <><span style={{ color: T.lightGray }}>Trạng thái:</span><span>{item.effectiveStatus === "approved" ? "Đã duyệt" : item.effectiveStatus === "unknown" ? "Chưa xác định" : item.effectiveStatus}</span></>}
      </div>
      {item.conflictNote && (
        <div style={{ marginTop: 8, padding: "6px 10px", background: T.errorSurface, borderRadius: 4, fontSize: 12, color: T.error }}>
          ⚠ {item.conflictNote}
        </div>
      )}
    </button>
  );
}

function evidenceColor(cls: string) {
  if (cls === "verified")   return { bg: T.softTeal,     border: T.green, text: T.interactive };
  if (cls === "conflicting") return { bg: T.errorSurface, border: T.error, text: T.error };
  if (cls === "missing")    return { bg: T.warnSurface,  border: T.orange, text: "#92400E" };
  if (cls === "stale")      return { bg: "#F5F5F5",      border: T.lightGray, text: T.secondary };
  return { bg: T.canvas, border: T.border, text: T.secondary };
}

function renderContent(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, i) =>
    p.startsWith("**") && p.endsWith("**")
      ? <strong key={i}>{p.slice(2, -2)}</strong>
      : <span key={i}>{p}</span>
  );
}

function buildInitialMessages(prompt: string): LocalMessage[] {
  if (!prompt) {
    return [{ id: "a-0", role: "assistant", content: "Bravo Agent AI có thể hỗ trợ anh/chị kiểm tra công việc nào?\n\nAnh/chị đang làm việc cho kỳ kế toán và công ty nào? Để có thể đánh giá điều kiện đóng kỳ, cần xác nhận phạm vi áp dụng trước.", evidenceRefs: [], isStreaming: false }];
  }
  return [
    { id: "u-0", role: "user", content: prompt, evidenceRefs: [] },
    { id: "a-0", role: "assistant", content: "", evidenceRefs: ["ev-1", "ev-3"], isStreaming: true },
  ];
}

function getAssistantReply(prompt: string): string {
  return `**Bravo Agent AI đang đối chiếu điều kiện và bằng chứng...**

Kết quả phân tích ban đầu dựa trên thông tin đã cung cấp:

**Yêu cầu được hiểu:** ${prompt}

**Lưu ý:** Phạm vi công ty và kỳ kế toán chưa được xác nhận. Đánh giá dưới đây là điều kiện chung — chưa được xác minh với dữ liệu thực của hệ thống.

**Điều kiện cần kiểm tra:**
- Chứng từ nguồn: Cần xác nhận tất cả đã được ghi nhận và phê duyệt
- Đối chiếu sổ phụ: Cần bằng chứng từ các sổ phụ liên quan
- Nghiệp vụ định kỳ: Cần xác nhận các nghiệp vụ áp dụng đã hoàn thành

**Hành động tiếp theo:** Xác nhận phạm vi công ty và kỳ kế toán cụ thể để có thể đánh giá chính xác hơn.

**Chưa đủ bằng chứng để xác nhận kết luận này.** Đây là bản nháp phân tích, chưa được thực hiện trên hệ thống.`;
}

function getFollowUpReply(): string {
  return `Bravo Agent AI đang đối chiếu điều kiện và bằng chứng...

Để có thể cung cấp đánh giá chính xác hơn, anh/chị vui lòng cung cấp thêm thông tin về phạm vi công ty và kỳ kế toán cụ thể.

**Chưa đủ bằng chứng để xác nhận kết luận này.**

Đây là bản nháp. Chưa được thực hiện trên hệ thống.`;
}
