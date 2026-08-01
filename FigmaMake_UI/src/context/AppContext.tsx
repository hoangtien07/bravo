import React, { createContext, useContext, useReducer, type ReactNode } from "react";
import type {
  TaskBrief, EnvironmentScope, UserRole, CapabilityState,
  PrerequisiteNode, EvidenceRef, DraftItem, DraftLifecycleStatus,
} from "../state/types";
import { UNKNOWN_SCOPE } from "../state/types";
import { getPrerequisites, EVIDENCE_ILLUSTRATION, DRAFT_ILLUSTRATION } from "../fixtures/scenarios";
import { fixtureId, fixtureNow } from "../fixtures/runtime";

// ── App state ─────────────────────────────────────────────────────────────

export type Screen = "new-conversation" | "active-conversation" | "conversations" | "financial-close"
  | "accounting-work"
  | "financial-graph" | "draft-approval" | "knowledge" | "admin" | "money-engine"
  | "anomaly" | "tax" | "knowledge-graph" | "review-index";

type AppState = {
  authenticated: boolean;
  screen: Screen;
  role: UserRole;
  capability: CapabilityState;
  scope: EnvironmentScope;
  task: TaskBrief | null;
  prerequisites: PrerequisiteNode[];
  evidence: EvidenceRef[];
  drafts: DraftItem[];
  conversationPrompt: string;
  taskEpoch: number;
  selectedEvidenceId: string | null;
  selectedPrerequisiteId: string | null;
  selectedDraftId: string | null;
};

type AppAction =
  | { type: "SIGN_IN" }
  | { type: "NAVIGATE"; screen: Screen }
  | { type: "SET_ROLE"; role: UserRole }
  | { type: "SET_CAPABILITY"; capability: CapabilityState }
  | { type: "START_CONVERSATION"; prompt: string }
  | { type: "PAUSE_TASK" }
  | { type: "CANCEL_TASK" }
  | { type: "RESUME_TASK" }
  | { type: "SWITCH_TASK"; prompt: string }
  | { type: "UPDATE_SCOPE"; scope: Partial<EnvironmentScope> }
  | { type: "SELECT_EVIDENCE"; id: string | null }
  | { type: "SELECT_PREREQUISITE"; id: string | null }
  | { type: "SELECT_DRAFT"; id: string | null }
  | { type: "DRAFT_ACTION"; draftId: string; action: "approve" | "reject" | "request_changes"; expectedRevision: number; note?: string }
  | { type: "LOAD_SCENARIO"; prerequisites: PrerequisiteNode[]; evidence: EvidenceRef[] };

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "SIGN_IN":
      return { ...state, authenticated: true };

    case "NAVIGATE":
      return { ...state, screen: action.screen };

    case "SET_ROLE":
      return { ...state, role: action.role };

    case "SET_CAPABILITY":
      return { ...state, capability: action.capability };

    case "START_CONVERSATION": {
      const financialCloseIntent = /đóng\s*kỳ|báo\s*cáo\s*tài\s*chính|bctc|đối\s*chiếu|cuối\s*kỳ/i.test(action.prompt);
      return {
        ...state,
        conversationPrompt: action.prompt,
        screen: "active-conversation",
        task: {
          taskId: fixtureId("task"),
          taskEpoch: state.taskEpoch,
          outcome: action.prompt,
          profile: "auto",
          status: financialCloseIntent ? "active" : "scoping",
          scope: state.scope,
          constraints: [],
          knownFacts: [],
          missingFacts: [
            { id: "scope-company", description: "Công ty áp dụng chưa được xác định" },
            { id: "scope-period", description: "Kỳ kế toán áp dụng chưa được xác định" },
          ],
          risk: financialCloseIntent ? "medium" : "low",
          revision: 1,
          createdAt: fixtureNow(),
        },
      };
    }

    case "PAUSE_TASK":
      if (!state.task) return state;
      return { ...state, task: { ...state.task, status: "paused" } };

    case "CANCEL_TASK":
      if (!state.task) return state;
      return { ...state, task: { ...state.task, status: "cancelled" } };

    case "RESUME_TASK":
      if (!state.task) return state;
      return { ...state, task: { ...state.task, status: "active" } };

    case "SWITCH_TASK":
      // New epoch: clear facts from previous task
      return {
        ...state,
        conversationPrompt: action.prompt,
        taskEpoch: state.taskEpoch + 1,
        task: {
          taskId: fixtureId("task"),
          taskEpoch: state.taskEpoch + 1,
          outcome: action.prompt,
          profile: "auto",
          status: "scoping",
          scope: state.scope,
          constraints: [],
          knownFacts: [],
          missingFacts: [],
          risk: "low",
          revision: 1,
          createdAt: fixtureNow(),
        },
        selectedEvidenceId: null,
      };

    case "UPDATE_SCOPE":
      return {
        ...state,
        scope: { ...state.scope, ...action.scope },
        task: state.task ? {
          ...state.task,
          scope: { ...state.task.scope, ...action.scope },
          revision: state.task.revision + 1,
        } : null,
        // Scope change marks prerequisites as needing reassessment
        prerequisites: state.prerequisites.map(p => ({
          ...p,
          status: p.status === "ready" ? "not_assessed" : p.status,
          reason: p.status === "ready" ? "Phạm vi vừa được cập nhật — cần đánh giá lại." : p.reason,
        })),
      };

    case "SELECT_EVIDENCE":
      return { ...state, selectedEvidenceId: action.id };

    case "SELECT_PREREQUISITE":
      return { ...state, selectedPrerequisiteId: action.id };

    case "SELECT_DRAFT":
      return { ...state, selectedDraftId: action.id };

    case "DRAFT_ACTION": {
      const statusMap: Record<string, DraftLifecycleStatus> = {
        approve: "approved",
        reject: "rejected",
        request_changes: "changes_requested",
      };
      return {
        ...state,
        drafts: state.drafts.map(d => {
          if (d.id !== action.draftId) return d;
          if (d.revision !== action.expectedRevision) return d;
          const allowedByStatus: Record<typeof action.action, DraftLifecycleStatus[]> = {
            approve: ["ready_for_review"],
            request_changes: ["ready_for_review", "validation_failed"],
            reject: ["ready_for_review", "validation_failed", "changes_requested"],
          };
          if (!allowedByStatus[action.action].includes(d.status)) return d;
          if (action.action === "approve" && ((d.validationIssues?.length ?? 0) > 0 || d.missingChecks.length > 0)) return d;
          if ((action.action === "request_changes" || action.action === "reject") && !action.note?.trim()) return d;
          const newStatus = statusMap[action.action] as DraftLifecycleStatus;
          const entry = {
            role: state.role === "administrator" ? "Quản trị viên" : "Kế toán trưởng",
            event: action.action === "approve" ? "Đã phê duyệt — chưa thực hiện trên hệ thống"
              : action.action === "reject" ? "Đã từ chối"
              : `Yêu cầu chỉnh sửa: ${action.note ?? "(không có ghi chú)"}`,
            timestampLabel: "[Vừa xong — minh họa]",
            revision: d.revision + 1,
            note: action.action === "approve" ? "Phê duyệt không đồng nghĩa đã thực hiện." : action.note,
          };
          return {
            ...d,
            status: newStatus,
            revision: d.revision + 1,
            changesRequestedNote: action.action === "request_changes" ? action.note : d.changesRequestedNote,
            rejectionReason: action.action === "reject" ? action.note : d.rejectionReason,
            auditTrail: [...d.auditTrail, entry],
          };
        }),
      };
    }

    case "LOAD_SCENARIO":
      return { ...state, prerequisites: action.prerequisites, evidence: action.evidence };

    default:
      return state;
  }
}

const initialState: AppState = {
  authenticated: false,
  screen: "new-conversation",
  role: "chief_accountant",
  capability: "online",
  scope: UNKNOWN_SCOPE,
  task: null,
  prerequisites: getPrerequisites("default_unknown"),
  evidence: EVIDENCE_ILLUSTRATION,
  drafts: DRAFT_ILLUSTRATION,
  conversationPrompt: "",
  taskEpoch: 1,
  selectedEvidenceId: null,
  selectedPrerequisiteId: null,
  selectedDraftId: DRAFT_ILLUSTRATION[0]?.id ?? null,
};

// ── Context ───────────────────────────────────────────────────────────────

type AppContextValue = {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
};

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  return <AppContext.Provider value={{ state, dispatch }}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppProvider");
  return ctx;
}
