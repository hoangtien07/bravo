export interface Identity {
  id: string;
  full_name: string;
  department_ids: string[];
  is_admin: boolean;
  permissions: string[];
}

export interface ConversationSummary {
  id: string;
  title: string;
  last_message_at: string | null;
  created_at: string;
}

export interface AccountingCaseView {
  case_id: string;
  case_type: string;
  state: string;
  revision: number;
  scope: Record<string, unknown>;
  evidence: { snapshot_id: string; source_type: string; source_version: string; complete: boolean }[];
  findings: { finding_id: string; finding_type: string; severity: string; status: string; check_result_ids: string[] }[];
  results: { check_id: string; reason_code: string; result: Record<string, string> }[];
  draft_payload_hash: string | null;
  approval: Record<string, unknown> | null;
}

export interface AccountingConversationReply {
  kind: "explanation" | "clarification" | "abstention";
  text: string;
  finding_ids: string[];
  evidence_snapshot_ids: string[];
  rule_ids: string[];
  mutates_case: false;
}

// Durable, caller-scoped workflow state exposed by Consultant Intelligence.
// It intentionally contains no transcript, source payload, or tool credentials.
export interface ConsultantState {
  task_epoch?: number;
  workflow_id: string | null;
  current_node: string | null;
  completed_nodes: string[];
  facts: Record<string, unknown>;
  open_questions: string[];
  status: "active" | "paused" | "completed" | "cancelled";
  revision: number;
  workflow_evidence_status?: "scaffold" | "sme_reviewed" | "verified" | null;
}

export type ConsultantProfile = "auto" | "bravo_user_guide" | "implementation" | "isms";
export type ConsultantFeedbackKind = "wrong_goal" | "wrong_step" | "unsafe_guidance";

export interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
  feedback?: "like" | "dislike" | null;
  // user message: attachments sent with the turn (filename + kind, for display)
  attachments?: { filename: string; kind: string }[];
  // assistant runtime extras (streaming)
  steps?: AgentStep[];
  citations?: string[];
  artifacts?: { id: string; kind: string; title: string }[];
  draft?: DraftEvent | null;
  grounded?: boolean;
  routedCloud?: boolean;
  clarify?: boolean;
  streaming?: boolean;
  statusText?: string;   // P1: transient "đang làm gì" line while streaming
}

// Chat-message attachment (v2 Track 3) — a staged/uploaded file for the current turn.
export interface Attachment {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  kind: "image" | "text";
  status: "pending" | "ready" | "failed";
  token_count?: number;
  error?: string | null;
}

// A staged attachment in the composer before/while it uploads.
export interface StagedAttachment {
  localId: string;
  id?: string;              // server id once uploaded
  name: string;
  kind: "image" | "text";
  status: "uploading" | "pending" | "ready" | "failed";
  previewUrl?: string;      // object URL for image thumbnails
  error?: string;
}

// Workspace document (v2 three-tier visibility).
export interface SourceItem {
  id: string;
  filename: string;
  status: string;
  knowledge_type?: string | null;
  visibility: "personal" | "department" | "global";
  owned: boolean;
  deduped?: boolean;
}

export interface AgentStep {
  type: "step" | "tool_call" | "tool_result" | "plan";
  action?: string;
  tool?: string;
  isError?: boolean;
  summary?: string;
  plan?: string[];
  args?: Record<string, unknown>;
}

export interface DraftEvent {
  draft_id?: string;
  kind?: string;
  payload?: JournalPayload | Record<string, unknown>;
}

export interface JournalLine {
  account: string;
  debit: string;
  credit: string;
  memo?: string;
  source_ref?: string;
}

export interface InvoiceLine {
  stt?: number | null;
  ten_hang?: string | null;
  dvt?: string | null;
  so_luong?: string | null;
  don_gia?: string | null;
  thanh_tien?: string | null;
  thue_suat?: string | null;
  tien_thue?: string | null;
}

export interface JournalPayload {
  doc_type?: string;
  invoice?: Record<string, unknown>;
  lines: JournalLine[];
  total_debit: string;
  total_credit: string;
  needs_review?: boolean;
  validation_flags?: string[];
  invoice_lines?: InvoiceLine[];
}

// SSE event union (khớp backend step_stream)
export type SseEvent =
  | { type: "id"; conversation_id: string; agent_run_id: string }
  | { type: "plan"; steps: string[] }
  | { type: "plan_update"; steps: string[] }
  | { type: "artifact"; artifact_id: string; kind: string; title: string }
  | { type: "source"; citations: string[] }
  | { type: "attachments"; items: { filename: string; kind: string }[] }
  | { type: "step"; action: string; step_n: number }
  | { type: "status"; text: string }
  | { type: "tool_call"; tool: string; args: Record<string, unknown> }
  | { type: "tool_result"; tool: string; isError: boolean; summary: string }
  | { type: "draft"; draft_id?: string; kind?: string; payload?: JournalPayload }
  | { type: "answer"; delta: string }
  | { type: "done"; grounded?: boolean; routed_cloud?: boolean; clarify?: boolean; stopped?: string; citations?: string[]; session_id?: string; message_id?: string; user_message_id?: string }
  | { type: "error"; message: string; code?: string }
  | { type: "ping" };

export interface Draft {
  id: string;
  kind: string;
  status: string;
  payload: JournalPayload | Record<string, unknown>;
  created_by?: string;
  created_at?: string;
}
