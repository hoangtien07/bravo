import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { createAuthApi, type AuthIdentity } from "../api/auth";
import { ApiError } from "../api/http";
import { CANDIDATE_TOKEN_KEY } from "../api/http";
import { useQA } from "../context/QAContext";

const CANDIDATE_RETURN_PATH_KEY = "bravo_v2_candidate_return_path";

type AuthStatus = "checking" | "anonymous" | "authenticated" | "unavailable";
export type AccountingCapabilities = { read: boolean; create: boolean; review: boolean };

type AuthContextValue = {
  status: AuthStatus;
  identity: AuthIdentity | null;
  oidcEnabled: boolean;
  error: string | null;
  capabilities: AccountingCapabilities;
  signInWithPassword(email: string, password: string): Promise<void>;
  consumeOidcFragment(): Promise<boolean>;
  beginOidc(returnPath: string): void;
  logout(): void;
  refresh(): Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function candidateStorage(): Storage | null {
  return typeof window === "undefined" ? null : window.sessionStorage;
}

function capability(identity: AuthIdentity | null, action: "read" | "create" | "review"): boolean {
  if (!identity) return false;
  if (identity.isAdmin) return true;
  return identity.permissions.some(permission => permission === "accounting_case:*" || permission === "accounting_case:*:*" || permission.startsWith(`accounting_case:${action}:`));
}

function safeReturnPath(path: string): string {
  return path.startsWith("/") && !path.startsWith("//") && !path.startsWith("/shared/") ? path : "/work";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("checking");
  const [identity, setIdentity] = useState<AuthIdentity | null>(null);
  const [oidcEnabled, setOidcEnabled] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const authApi = useMemo(() => createAuthApi(), []);
  const { qa } = useQA();

  const clearSession = useCallback(() => {
    candidateStorage()?.removeItem(CANDIDATE_TOKEN_KEY);
    setIdentity(null);
  }, []);

  const refresh = useCallback(async () => {
    const token = candidateStorage()?.getItem(CANDIDATE_TOKEN_KEY);
    if (!token) { setStatus("anonymous"); setIdentity(null); return; }
    setStatus("checking");
    try {
      const nextIdentity = await authApi.me(token);
      setIdentity(nextIdentity);
      setError(null);
      setStatus("authenticated");
    } catch (reason) {
      if (reason instanceof ApiError && reason.kind === "unauthorized") {
        clearSession();
        setError("Phiên đã hết hạn. Hãy đăng nhập lại để tiếp tục.");
        setStatus("anonymous");
        return;
      }
      setError(reason instanceof Error ? reason.message : "Không thể xác minh phiên đăng nhập.");
      setStatus("unavailable");
    }
  }, [authApi, clearSession]);

  useEffect(() => {
    if (qa.enabled) {
      setStatus("anonymous");
      setIdentity(null);
      setError(null);
      return;
    }
    void authApi.config().then(config => setOidcEnabled(config.oidcEnabled)).catch(reason => setError(reason instanceof Error ? reason.message : "Không thể tải cấu hình xác thực."));
    void refresh();
  }, [authApi, qa.enabled, refresh]);

  const establish = useCallback(async (token: string) => {
    candidateStorage()?.setItem(CANDIDATE_TOKEN_KEY, token);
    try {
      const nextIdentity = await authApi.me(token);
      setIdentity(nextIdentity);
      setError(null);
      setStatus("authenticated");
    } catch (reason) {
      clearSession();
      setStatus("anonymous");
      throw reason;
    }
  }, [authApi, clearSession]);

  const value = useMemo<AuthContextValue>(() => ({
    status, identity, oidcEnabled, error,
    capabilities: { read: capability(identity, "read"), create: capability(identity, "create"), review: capability(identity, "review") },
    async signInWithPassword(email, password) { await establish(await authApi.passwordLogin(email, password)); },
    async consumeOidcFragment() {
      const token = new URLSearchParams(window.location.hash.replace(/^#/, "")).get("token");
      if (!token) return false;
      window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
      await establish(token);
      return true;
    },
    beginOidc(returnPath) {
      candidateStorage()?.setItem(CANDIDATE_RETURN_PATH_KEY, safeReturnPath(returnPath));
      window.location.assign("/api/auth/oidc/login");
    },
    logout() { clearSession(); setError(null); setStatus("anonymous"); },
    refresh,
  }), [authApi, clearSession, establish, error, identity, oidcEnabled, refresh, status]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function consumeSavedReturnPath(): string {
  const value = candidateStorage()?.getItem(CANDIDATE_RETURN_PATH_KEY) ?? "/work";
  candidateStorage()?.removeItem(CANDIDATE_RETURN_PATH_KEY);
  return safeReturnPath(value);
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
