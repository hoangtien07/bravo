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

export interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
  feedback?: "like" | "dislike" | null;
  // assistant runtime extras (streaming)
  steps?: AgentStep[];
  citations?: string[];
  draft?: DraftEvent | null;
  grounded?: boolean;
  routedCloud?: boolean;
  clarify?: boolean;
  streaming?: boolean;
}

export interface AgentStep {
  type: "step" | "tool_call" | "tool_result";
  action?: string;
  tool?: string;
  isError?: boolean;
  summary?: string;
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

export interface JournalPayload {
  doc_type?: string;
  invoice?: Record<string, unknown>;
  lines: JournalLine[];
  total_debit: string;
  total_credit: string;
  needs_review?: boolean;
  validation_flags?: string[];
}

// SSE event union (khớp backend step_stream)
export type SseEvent =
  | { type: "id"; conversation_id: string; agent_run_id: string }
  | { type: "source"; citations: string[] }
  | { type: "step"; action: string; step_n: number }
  | { type: "tool_call"; tool: string; args: Record<string, unknown> }
  | { type: "tool_result"; tool: string; isError: boolean; summary: string }
  | { type: "draft"; draft_id?: string; kind?: string; payload?: JournalPayload }
  | { type: "answer"; delta: string }
  | { type: "done"; grounded?: boolean; routed_cloud?: boolean; clarify?: boolean; stopped?: string; citations?: string[]; session_id?: string }
  | { type: "error"; message: string }
  | { type: "ping" };

export interface Draft {
  id: string;
  kind: string;
  status: string;
  payload: JournalPayload | Record<string, unknown>;
  created_by?: string;
  created_at?: string;
}
