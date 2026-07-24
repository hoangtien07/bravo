import React from "react";
import type { PrerequisiteStatus, DraftLifecycleStatus, EvidenceClass } from "../state/types";
import { DRAFT_STATUS_CONFIG, EVIDENCE_CLASS_CONFIG } from "../state/types";

// ── Design tokens (runtime JS mirror of CSS vars) ─────────────────────────
export const T = {
  green:          "var(--brand-green)",
  interactive:    "var(--interactive)",
  interactiveHov: "var(--interactive-hover)",
  softTeal:       "var(--soft-teal)",
  canvas:         "var(--canvas)",
  strong:         "var(--strong)",
  secondary:      "var(--secondary)",
  border:         "var(--border)",
  orange:         "#FBAF3F",
  warnSurface:    "var(--warning-surface)",
  warningText:    "var(--warning-text)",
  error:          "var(--error)",
  errorSurface:   "var(--error-surface)",
  info:           "#175CD3",
  lightGray:      "var(--light-gray)",
  white:          "var(--surface)",
} as const;

// ── Diagonal // motif (29°) ────────────────────────────────────────────────
interface DiagonalMotifProps {
  color?: string;
  size?: number;
  className?: string;
}
export function DiagonalMotif({ color = T.green, size = 24, className = "" }: DiagonalMotifProps) {
  const angle = 29;
  const rad = (angle * Math.PI) / 180;
  const h = size;
  const w = size * 0.45;
  const gap = w * 0.6;
  const totalW = w * 2 + gap;
  return (
    <svg
      width={totalW} height={h}
      viewBox={`0 0 ${totalW} ${h}`}
      aria-hidden="true"
      className={className}
      style={{ display: "inline-block", verticalAlign: "middle", flexShrink: 0 }}
    >
      {[0, w + gap].map((x, i) => (
        <line key={i}
          x1={x + h * Math.tan(rad)} y1={0}
          x2={x} y2={h}
          stroke={color}
          strokeWidth={Math.max(1.5, size * 0.09)}
          strokeLinecap="round"
        />
      ))}
    </svg>
  );
}

// ── Status badge (evidence/prerequisite) ──────────────────────────────────
export type EvidenceStatus =
  | "not-assessed" | "missing" | "in-progress" | "ready"
  | "conflict" | "not-applicable" | "draft" | "approved"
  | "executed" | "verified" | "blocked" | "stale";

const BADGE_CFG: Record<EvidenceStatus, { label: string; icon: string; bg: string; text: string; border: string }> = {
  "not-assessed":   { label: "Chưa đánh giá",          icon: "○",  bg: T.canvas,       text: T.secondary,  border: T.border      },
  "missing":        { label: "Thiếu bằng chứng",       icon: "⚠",  bg: T.warnSurface,  text: T.warningText, border: T.orange      },
  "in-progress":    { label: "Đang xử lý",             icon: "◑",  bg: T.softTeal,     text: T.interactive,border: T.green       },
  "ready":          { label: "Sẵn sàng",               icon: "✓",  bg: T.softTeal,     text: T.interactive,border: T.green       },
  "conflict":       { label: "Xung đột",               icon: "✕",  bg: T.errorSurface, text: T.error,      border: T.error       },
  "not-applicable": { label: "Không áp dụng",          icon: "—",  bg: T.canvas,       text: T.secondary,  border: T.border      },
  "draft":          { label: "NHÁP",                   icon: "✎",  bg: T.warnSurface,  text: T.warningText, border: T.orange      },
  "approved":       { label: "Đã phê duyệt",           icon: "✓",  bg: T.softTeal,     text: T.interactive,border: T.green       },
  "executed":       { label: "Đã thực hiện",           icon: "⊙",  bg: "#F0F4FF",      text: "#1D4ED8",    border: "#93C5FD"     },
  "verified":       { label: "Đã xác minh kết quả",    icon: "✔",  bg: T.softTeal,     text: T.interactive,border: T.green       },
  "blocked":        { label: "Bị chặn",                icon: "⛔", bg: T.errorSurface,  text: T.error,      border: T.error       },
  "stale":          { label: "Đã lỗi thời",            icon: "⏱",  bg: "#F5F5F5",      text: T.secondary,  border: T.lightGray   },
};

export function prereqStatusToEvidenceStatus(s: PrerequisiteStatus): EvidenceStatus {
  const map: Record<PrerequisiteStatus, EvidenceStatus> = {
    not_assessed:     "not-assessed",
    missing_evidence: "missing",
    in_progress:      "in-progress",
    ready:            "ready",
    conflict:         "conflict",
    not_applicable:   "not-applicable",
    blocked:          "blocked",
  };
  return map[s];
}

export function draftStatusToEvidenceStatus(s: DraftLifecycleStatus): EvidenceStatus {
  const map: Record<DraftLifecycleStatus, EvidenceStatus> = {
    proposed_draft:             "draft",
    validating:                 "in-progress",
    validation_failed:          "conflict",
    ready_for_review:           "in-progress",
    changes_requested:          "missing",
    rejected:                   "conflict",
    approved:                   "approved",
    exported_for_manual_action: "in-progress",
    externally_executed:        "executed",
    verified:                   "verified",
  };
  return map[s];
}

interface StatusBadgeProps {
  status: EvidenceStatus;
  compact?: boolean;
}
export function StatusBadge({ status, compact = false }: StatusBadgeProps) {
  const cfg = BADGE_CFG[status];
  return (
    <span role="status" style={{
      background: cfg.bg, color: cfg.text, border: `1px solid ${cfg.border}`,
      borderRadius: 4, padding: compact ? "1px 6px" : "2px 8px",
      fontSize: compact ? 11 : 12, fontWeight: 500,
      display: "inline-flex", alignItems: "center", gap: 4, whiteSpace: "nowrap",
    }}>
      <span aria-hidden="true">{cfg.icon}</span>
      <span>{cfg.label}</span>
    </span>
  );
}

// ── Draft lifecycle badge ─────────────────────────────────────────────────
export function DraftLifecycleBadge({ status }: { status: DraftLifecycleStatus }) {
  const cfg = DRAFT_STATUS_CONFIG[status];
  return (
    <span role="status" style={{
      background: cfg.bg, color: cfg.text, border: `1px solid ${cfg.border}`,
      borderRadius: 4, padding: "2px 8px", fontSize: 12, fontWeight: 500,
      display: "inline-flex", alignItems: "center", gap: 4, whiteSpace: "nowrap",
    }}>
      <span aria-hidden="true">{cfg.icon}</span>
      {cfg.label}
    </span>
  );
}

// ── Evidence class badge ──────────────────────────────────────────────────
export function EvidenceClassBadge({ cls }: { cls: EvidenceClass }) {
  const cfg = EVIDENCE_CLASS_CONFIG[cls];
  return (
    <span style={{ fontSize: 11, fontWeight: 500, color: cfg.color, display: "inline-flex", alignItems: "center", gap: 3 }}>
      <span aria-hidden="true">{cfg.icon}</span>{cfg.label}
    </span>
  );
}

// ── Button ────────────────────────────────────────────────────────────────
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
  loading?: boolean;
}
export function Button({ variant = "primary", size = "md", loading, children, style, disabled, ...rest }: ButtonProps) {
  const base: React.CSSProperties = {
    display: "inline-flex", alignItems: "center", gap: 6, borderRadius: 6,
    fontWeight: 500, cursor: disabled || loading ? "not-allowed" : "pointer",
    border: "1px solid transparent", transition: "background 150ms, border-color 150ms",
    fontSize: size === "sm" ? 13 : 14,
    padding: size === "sm" ? "5px 12px" : "8px 16px",
    fontFamily: "inherit", minHeight: 36,
    opacity: disabled || loading ? 0.55 : 1,
  };
  const variants: Record<string, React.CSSProperties> = {
    primary:   { background: T.interactive,   color: T.white,      borderColor: T.interactive   },
    secondary: { background: T.white,         color: T.interactive, borderColor: T.border       },
    ghost:     { background: "transparent",   color: T.secondary,  borderColor: "transparent"  },
    danger:    { background: T.errorSurface,  color: T.error,      borderColor: T.error        },
  };
  return (
    <button
      disabled={disabled || loading}
      style={{ ...base, ...variants[variant], ...style }}
      {...rest}
    >
      {loading ? <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
        <span style={{ width: 10, height: 10, border: "2px solid currentColor", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.7s linear infinite", display: "inline-block" }} />
        {children}
      </span> : children}
    </button>
  );
}

// ── Input ─────────────────────────────────────────────────────────────────
export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      style={{
        width: "100%", padding: "8px 12px", borderRadius: 6,
        border: "1px solid #D7E1DE", fontSize: 14, fontFamily: "inherit",
        background: "#fff", color: "#1F2927", outline: "none",
        transition: "border-color 150ms", minHeight: 44,
        ...props.style,
      }}
      onFocus={e => { e.currentTarget.style.borderColor = T.interactive; props.onFocus?.(e); }}
      onBlur={e => { e.currentTarget.style.borderColor = T.border; props.onBlur?.(e); }}
    />
  );
}

// ── Textarea ──────────────────────────────────────────────────────────────
export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      style={{
        width: "100%", padding: "8px 12px", borderRadius: 6,
        border: "1px solid #D7E1DE", fontSize: 14, fontFamily: "inherit",
        background: "#fff", color: "#1F2927", outline: "none",
        transition: "border-color 150ms", resize: "vertical", minHeight: 80,
        ...props.style,
      }}
      onFocus={e => { e.currentTarget.style.borderColor = T.interactive; props.onFocus?.(e); }}
      onBlur={e => { e.currentTarget.style.borderColor = T.border; props.onBlur?.(e); }}
    />
  );
}

// ── Empty / Error / Permission states ────────────────────────────────────
interface StateCardProps { title: string; body: string; action?: React.ReactNode; icon?: string; }

export function EmptyState({ title, body, action, icon = "○" }: StateCardProps) {
  return (
    <div role="status" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "48px 24px", textAlign: "center", gap: 12 }}>
      <div style={{ fontSize: 32, color: T.lightGray }}>{icon}</div>
      <p style={{ margin: 0, fontSize: 16, fontWeight: 600, color: T.strong }}>{title}</p>
      <p style={{ margin: 0, fontSize: 14, color: T.secondary, maxWidth: 360 }}>{body}</p>
      {action}
    </div>
  );
}

export function ErrorState({ title, body, action }: StateCardProps) {
  return (
    <div role="alert" style={{ margin: "24px auto", maxWidth: 480, padding: "20px 24px", background: T.errorSurface, border: `1px solid ${T.error}`, borderRadius: 8, textAlign: "center" }}>
      <p style={{ margin: "0 0 6px", fontSize: 14, fontWeight: 600, color: T.error }}>✕ {title}</p>
      <p style={{ margin: "0 0 12px", fontSize: 13, color: T.error }}>{body}</p>
      {action}
    </div>
  );
}

export function PermissionDeniedState({ message }: { message?: string }) {
  return (
    <div role="alert" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "48px 24px", textAlign: "center", gap: 12 }}>
      <div style={{ fontSize: 32, color: T.lightGray }}>⊘</div>
      <p style={{ margin: 0, fontSize: 16, fontWeight: 600, color: T.strong }}>Không có quyền truy cập</p>
      <p style={{ margin: 0, fontSize: 14, color: T.secondary, maxWidth: 360 }}>
        {message ?? "Một phần đường dẫn không khả dụng theo phạm vi truy cập của anh/chị."}
      </p>
      <p style={{ margin: 0, fontSize: 12, color: T.lightGray }}>Liên hệ quản trị viên để được cấp quyền.</p>
    </div>
  );
}

export function OfflineState({ localAvailable }: { localAvailable?: boolean }) {
  return (
    <div style={{ padding: "12px 16px", background: T.warnSurface, border: `1px solid ${T.orange}`, borderRadius: 8, display: "flex", gap: 10, alignItems: "flex-start" }}>
      <span aria-hidden="true" style={{ color: "#92400E", fontSize: 16 }}>⚡</span>
      <div>
        <p style={{ margin: "0 0 2px", fontSize: 13, fontWeight: 600, color: "#92400E" }}>
          {localAvailable ? "Chế độ ngoại tuyến — khả năng giới hạn" : "Không có kết nối"}
        </p>
        <p style={{ margin: 0, fontSize: 12, color: "#92400E" }}>
          {localAvailable
            ? "Tư vấn cục bộ vẫn khả dụng. Một số bằng chứng cần kết nối để xác minh."
            : "Không thể kết nối. Kiểm tra kết nối mạng và thử lại."}
        </p>
      </div>
    </div>
  );
}

// ── Inline banner / alert ─────────────────────────────────────────────────
type BannerVariant = "info" | "warning" | "error" | "success" | "draft";
const BANNER_CFG: Record<BannerVariant, { bg: string; border: string; text: string; icon: string }> = {
  info:    { bg: "#EFF6FF", border: "#175CD3", text: "#175CD3", icon: "ℹ" },
  warning: { bg: T.warnSurface,  border: T.orange, text: T.warningText, icon: "⚠" },
  error:   { bg: T.errorSurface, border: T.error,  text: T.error,   icon: "✕" },
  success: { bg: T.softTeal,     border: T.green,  text: T.interactive, icon: "✓" },
  draft:   { bg: T.warnSurface,  border: T.orange, text: T.warningText, icon: "✎" },
};
export function Banner({ variant, children }: { variant: BannerVariant; children: React.ReactNode }) {
  const cfg = BANNER_CFG[variant];
  return (
    <div role={variant === "error" ? "alert" : "status"} style={{ display: "flex", gap: 10, padding: "10px 14px", background: cfg.bg, border: `1px solid ${cfg.border}`, borderRadius: 6 }}>
      <span aria-hidden="true" style={{ color: cfg.text, flexShrink: 0, fontSize: 14 }}>{cfg.icon}</span>
      <div style={{ fontSize: 13, color: cfg.text, lineHeight: "20px" }}>{children}</div>
    </div>
  );
}

// ── Loading skeleton ──────────────────────────────────────────────────────
export function SkeletonRow({ width = "100%", height = 16 }: { width?: string | number; height?: number }) {
  return (
    <div
      aria-hidden="true"
      style={{
        width, height, borderRadius: 4,
        background: `linear-gradient(90deg, ${T.border} 25%, #E8F0ED 50%, ${T.border} 75%)`,
        backgroundSize: "200% 100%",
        animation: "shimmer 1.4s infinite",
      }}
    />
  );
}

export function SkeletonBlock() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }} aria-label="Đang tải..." aria-busy="true">
      <SkeletonRow width="60%" height={20} />
      <SkeletonRow width="100%" />
      <SkeletonRow width="85%" />
      <SkeletonRow width="40%" height={12} />
    </div>
  );
}

// ── Divider ───────────────────────────────────────────────────────────────
export function Divider({ vertical = false }: { vertical?: boolean }) {
  return <div aria-hidden="true" style={{ background: T.border, ...(vertical ? { width: 1, alignSelf: "stretch" } : { height: 1 }) }} />;
}

// ── QA illustration label ─────────────────────────────────────────────────
export function IllustrationLabel() {
  return (
    <div style={{ padding: "3px 8px", background: "#FFF9C4", border: "1px solid #F59E0B", borderRadius: 3, fontSize: 10, fontWeight: 700, color: "#92400E", letterSpacing: "0.04em", display: "inline-block" }}>
      DỮ LIỆU MINH HỌA — KHÔNG PHẢI DỮ LIỆU THỰC
    </div>
  );
}

// ── Scope chips ───────────────────────────────────────────────────────────
import type { KnownOrUnknown } from "../state/types";

export function ScopeChip({ label, value }: { label: string; value: KnownOrUnknown }) {
  const known = value.known;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 12 }}>
      <span style={{ color: T.lightGray }}>{label}:</span>
      <span style={{ color: known ? T.strong : T.lightGray, fontWeight: known ? 500 : 400, fontStyle: known ? "normal" : "italic" }}>
        {known ? value.value : "Chưa xác định"}
      </span>
    </span>
  );
}

// ── Focus trap hook ───────────────────────────────────────────────────────
export function useFocusTrap(ref: React.RefObject<HTMLElement | null>, active: boolean) {
  React.useEffect(() => {
    if (!active || !ref.current) return;
    const el = ref.current;
    const focusable = el.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    first?.focus();
    function handler(e: KeyboardEvent) {
      if (e.key !== "Tab") return;
      if (e.shiftKey) { if (document.activeElement === first) { e.preventDefault(); last?.focus(); } }
      else { if (document.activeElement === last) { e.preventDefault(); first?.focus(); } }
    }
    el.addEventListener("keydown", handler);
    return () => el.removeEventListener("keydown", handler);
  }, [active, ref]);
}
