import { createContext, useContext, useState, type ReactNode } from "react";
import type { CapabilityState, QAComponentState, QASettings, UserRole } from "../state/types";
import { DEFAULT_QA } from "../state/types";
import { getPrerequisites, EVIDENCE_ILLUSTRATION } from "../fixtures/scenarios";
import { useApp } from "./AppContext";

const QAContext = createContext<{
  qa: QASettings;
  setQA: (patch: Partial<QASettings>) => void;
} | null>(null);

export function QAProvider({ children }: { children: ReactNode }) {
  const [qa, setQAState] = useState<QASettings>(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("qa") === "1") {
      const rawState = params.get("state");
      const states: QAComponentState[] = ["default", "loading", "empty", "error", "permission_denied", "stale", "conflict", "success", "offline", "session_expired", "revision_conflict"];
      return {
        ...DEFAULT_QA,
        enabled: true,
        role: (params.get("role") as UserRole) || DEFAULT_QA.role,
        capability: (params.get("capability") as CapabilityState) || DEFAULT_QA.capability,
        scenario: params.get("scenario") || DEFAULT_QA.scenario,
        componentState: states.includes(rawState as QAComponentState) ? rawState as QAComponentState : "default",
      };
    }
    return DEFAULT_QA;
  });

  const { dispatch } = useApp();

  function setQA(patch: Partial<QASettings>) {
    setQAState(prev => {
      const next = { ...prev, ...patch };
      // When scenario changes, load fixture data
      if (patch.scenario) {
        dispatch({
          type: "LOAD_SCENARIO",
          prerequisites: getPrerequisites(patch.scenario),
          evidence: EVIDENCE_ILLUSTRATION,
        });
      }
      if (patch.role) {
        dispatch({ type: "SET_ROLE", role: patch.role });
      }
      if (patch.capability) {
        dispatch({ type: "SET_CAPABILITY", capability: patch.capability });
      }
      const params = new URLSearchParams(window.location.search);
      params.set("qa", next.enabled ? "1" : "0");
      params.set("role", next.role);
      params.set("capability", next.capability);
      params.set("scenario", next.scenario);
      params.set("state", next.componentState);
      window.history.replaceState(null, "", `${window.location.pathname}?${params}${window.location.hash}`);
      return next;
    });
  }

  return <QAContext.Provider value={{ qa, setQA }}>{children}</QAContext.Provider>;
}

export function useQA() {
  const ctx = useContext(QAContext);
  if (!ctx) throw new Error("useQA must be inside QAProvider");
  return ctx;
}
