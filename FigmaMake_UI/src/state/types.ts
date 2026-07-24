// ── Utility types ─────────────────────────────────────────────────────────
export type KnownOrUnknown<T = string> =
  | { known: true; value: T }
  | { known: false };

// ── User/role ─────────────────────────────────────────────────────────────
export type UserRole =
  | "accountant"
  | "chief_accountant"
  | "finance_manager"
  | "consultant"
  | "administrator";

export type CapabilityState =
  | "online"
  | "offline_local"
  | "limited_capability"
  | "cloud_blocked";

export type UserPermissions = {
  canApprove: boolean;
  canAdminister: boolean;
  canViewKnowledge: boolean;
  canViewGraph: boolean;
};

export const ROLE_PERMISSIONS: Record<UserRole, UserPermissions> = {
  accountant:       { canApprove: false, canAdminister: false, canViewKnowledge: true,  canViewGraph: false },
  chief_accountant: { canApprove: true,  canAdminister: false, canViewKnowledge: true,  canViewGraph: true  },
  finance_manager:  { canApprove: true,  canAdminister: false, canViewKnowledge: true,  canViewGraph: true  },
  consultant:       { canApprove: false, canAdminister: false, canViewKnowledge: true,  canViewGraph: true  },
  administrator:    { canApprove: true,  canAdminister: true,  canViewKnowledge: true,  canViewGraph: true  },
};

// ── Environment scope ─────────────────────────────────────────────────────
export type EnvironmentScope = {
  company: KnownOrUnknown;
  branch: KnownOrUnknown;
  accountingPeriod: KnownOrUnknown;
  bravoVersion: KnownOrUnknown;
  environment: KnownOrUnknown;
};

export const UNKNOWN_SCOPE: EnvironmentScope = {
  company:          { known: false },
  branch:           { known: false },
  accountingPeriod: { known: false },
  bravoVersion:     { known: false },
  environment:      { known: false },
};

export function scopeLabel(field: KnownOrUnknown): string {
  return field.known ? field.value : "Chưa xác định";
}

// ── Task ──────────────────────────────────────────────────────────────────
export type TaskStatus = "scoping" | "active" | "paused" | "completed" | "cancelled";
export type TaskProfile = "auto" | "business" | "technical";

export type FactRef = {
  evidenceId: string;
  claim: string;
};

export type MissingFact = {
  id: string;
  description: string;
};

export type TaskBrief = {
  taskId: string;
  taskEpoch: number;
  outcome: string;
  profile: TaskProfile;
  status: TaskStatus;
  scope: EnvironmentScope;
  constraints: string[];
  knownFacts: FactRef[];
  missingFacts: MissingFact[];
  risk: "low" | "medium" | "high";
  revision: number;
  createdAt: string;
};

// ── Evidence ──────────────────────────────────────────────────────────────
export type EvidenceClass =
  | "user_supplied"
  | "inferred"
  | "verified"
  | "conflicting"
  | "missing"
  | "stale";

export type EvidenceRef = {
  id: string;
  claim: string;
  evidenceClass: EvidenceClass;
  sourceName?: string;
  locator?: string;
  company?: string;
  period?: string;
  environment?: string;
  bravoVersion?: string;
  effectiveStatus?: "unknown" | "candidate" | "approved" | "superseded";
  freshness?: "current" | "stale" | "unknown";
  conflictNote?: string;
};

export const EVIDENCE_CLASS_CONFIG: Record<EvidenceClass, { label: string; icon: string; color: string }> = {
  user_supplied: { label: "Người dùng cung cấp", icon: "○", color: "#56625F" },
  inferred:      { label: "Suy luận",            icon: "◑", color: "#006B5D" },
  verified:      { label: "Đã xác minh",         icon: "✓", color: "#006B5D" },
  conflicting:   { label: "Xung đột",            icon: "✕", color: "#B42318" },
  missing:       { label: "Thiếu",               icon: "⚠", color: "#92400E" },
  stale:         { label: "Đã lỗi thời",         icon: "⏱", color: "#56625F" },
};

// ── Prerequisites ─────────────────────────────────────────────────────────
export type PrerequisiteStatus =
  | "not_assessed"
  | "missing_evidence"
  | "in_progress"
  | "ready"
  | "conflict"
  | "not_applicable"
  | "blocked";

export type PrerequisiteNode = {
  id: string;
  step: number;
  title: string;
  description: string;
  prerequisiteIds: string[];
  applicability: "unknown" | "applicable" | "not_applicable";
  status: PrerequisiteStatus;
  reason: string;
  evidenceRefs: string[];
  missingEvidence: string[];
  responsibleRole?: string;
  nextSafeAction?: string;
  completionSignal?: string;
};

// ── Draft lifecycle ───────────────────────────────────────────────────────
export type DraftLifecycleStatus =
  | "proposed_draft"
  | "validating"
  | "validation_failed"
  | "ready_for_review"
  | "changes_requested"
  | "rejected"
  | "approved"
  | "exported_for_manual_action"
  | "externally_executed"
  | "verified";

export const DRAFT_STATUS_CONFIG: Record<DraftLifecycleStatus, {
  label: string;
  icon: string;
  bg: string;
  text: string;
  border: string;
}> = {
  proposed_draft:             { label: "Bản nháp đề xuất",       icon: "✎", bg: "#FFF4DE", text: "#92400E", border: "#FBAF3F" },
  validating:                 { label: "Đang kiểm tra",          icon: "◑", bg: "#E8F7F4", text: "#006B5D", border: "#00A88D" },
  validation_failed:          { label: "Kiểm tra thất bại",      icon: "✕", bg: "#FDECEA", text: "#B42318", border: "#B42318" },
  ready_for_review:           { label: "Chờ xem xét",            icon: "→", bg: "#EFF6FF", text: "#175CD3", border: "#175CD3" },
  changes_requested:          { label: "Yêu cầu chỉnh sửa",     icon: "↩", bg: "#FFF4DE", text: "#92400E", border: "#FBAF3F" },
  rejected:                   { label: "Đã từ chối",             icon: "✕", bg: "#FDECEA", text: "#B42318", border: "#B42318" },
  approved:                   { label: "Đã phê duyệt",          icon: "✓", bg: "#E8F7F4", text: "#006B5D", border: "#00A88D" },
  exported_for_manual_action: { label: "Đã xuất — chờ nhập thủ công", icon: "↗", bg: "#F6F9F8", text: "#56625F", border: "#D7E1DE" },
  externally_executed:        { label: "Đã thực hiện bên ngoài", icon: "⊙", bg: "#F6F9F8", text: "#56625F", border: "#D7E1DE" },
  verified:                   { label: "Đã xác minh kết quả",    icon: "✔", bg: "#E8F7F4", text: "#006B5D", border: "#00A88D" },
};

export type AuditEntry = {
  role: string;
  event: string;
  timestampLabel: string;
  revision: number;
  note?: string;
};

export type DraftItem = {
  id: string;
  title: string;
  purpose: string;
  scope: string;
  beforeState: string;
  afterState: string;
  risk: string;
  missingChecks: string[];
  status: DraftLifecycleStatus;
  requesterRole: string;
  reviewerRole?: string;
  revision: number;
  auditTrail: AuditEntry[];
  evidenceRefs: string[];
  changesRequestedNote?: string;
  rejectionReason?: string;
  validationIssues?: string[];
};

// ── Knowledge document ────────────────────────────────────────────────────
export type DocType = "Quy trình nội bộ" | "Văn bản pháp lý" | "Hướng dẫn BRAVO" | "Bằng chứng kiểm toán";
export type DocApprovalStatus = "approved" | "draft" | "conflict" | "not_available";
export type DocIngestionStatus = "completed" | "in_progress" | "failed" | "missing" | "not_applicable";

export type KnowledgeDoc = {
  id: string;
  name: string;
  type: DocType;
  owner: string;
  bravoVersion: KnownOrUnknown;
  effectiveDate: KnownOrUnknown;
  approvalStatus: DocApprovalStatus;
  visibility: string;
  ingestionStatus: DocIngestionStatus;
  traceability: KnownOrUnknown;
  supersededBy?: string;
  supersedes?: string;
  conflictNote?: string;
  ingestionError?: string;
};

// ── Conversation message ──────────────────────────────────────────────────
export type MessageRole = "user" | "assistant" | "system";

export type AnswerSection = {
  heading: string;
  body: string;
  evidenceRefs: string[];
};

export type AnswerDraft = {
  understoodOutcome: string;
  applicablePrerequisites: AnswerSection[];
  nextAction: string;
  uncertainty: string[];
  clarification?: string;
  evidenceRefs: string[];
};

export type ConversationMessage = {
  id: string;
  role: MessageRole;
  content: string;
  answer?: AnswerDraft;
  evidenceRefs: string[];
  timestamp: string;
  isStreaming?: boolean;
};

// ── QA mode ───────────────────────────────────────────────────────────────
export type QAScenario = string;

export type QAComponentState =
  | "default"
  | "loading"
  | "empty"
  | "error"
  | "permission_denied"
  | "stale"
  | "conflict"
  | "success"
  | "offline"
  | "session_expired"
  | "revision_conflict";

export type QASettings = {
  enabled: boolean;
  role: UserRole;
  capability: CapabilityState;
  scenario: QAScenario;
  componentState: QAComponentState;
};

export const DEFAULT_QA: QASettings = {
  enabled: false,
  role: "chief_accountant",
  capability: "online",
  scenario: "default_unknown",
  componentState: "default",
};
