import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { setUnauthorizedHandler } from "@/api/client";
import { useAuth } from "@/store/auth";
import { AppShell } from "@/features/chat/AppShell";
import { ChatView } from "@/features/chat/ChatView";
import { AuiChatView } from "@/features/chat/AuiChatView";
import { MoneyEnginePage } from "@/features/money/MoneyEnginePage";
import { GraphView } from "@/features/graph/GraphView";
import { AnomalyPage } from "@/features/anomaly/AnomalyPage";
import { TaxPage } from "@/features/tax/TaxPage";
import { DraftsQueuePage } from "@/features/drafts/DraftsQueuePage";
import { DocumentsPage } from "@/features/documents/DocumentsPage";
import { AdminPage } from "@/features/admin/AdminPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { SharedPage } from "@/features/shared/SharedPage";

function Protected({ children }: { children: React.ReactNode }) {
  const { identity, loading } = useAuth();
  const location = useLocation();
  // Keep the original SPA URL across authentication. In particular, this means
  // `/?ui=beta` reaches the beta selector after a user signs in.
  if (!identity && !loading) {
    const next = encodeURIComponent(`${location.pathname}${location.search}`);
    return <Navigate to={`/login?next=${next}`} replace />;
  }
  return <>{children}</>;
}

// P2: assistant-ui surface behind a flag — `?ui=beta` (sticky), or VITE_ASSISTANT_UI=1 at build.
// Legacy ChatView stays the default until parity is confirmed.
function useChatSurface() {
  if (typeof window !== "undefined") {
    const q = new URLSearchParams(window.location.search).get("ui");
    if (q === "beta") localStorage.setItem("bravo_ui", "beta");
    if (q === "classic") localStorage.removeItem("bravo_ui");
    if (localStorage.getItem("bravo_ui") === "beta") return AuiChatView;
  }
  return import.meta.env.VITE_ASSISTANT_UI === "1" ? AuiChatView : ChatView;
}

export default function App() {
  const { identity, loadMe } = useAuth();
  const nav = useNavigate();
  const Chat = useChatSurface();

  useEffect(() => {
    setUnauthorizedHandler(() => nav("/login"));
    loadMe();
  }, []);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/shared/:token" element={<SharedPage />} />
      <Route element={<Protected><AppShell /></Protected>}>
        <Route path="/" element={<Chat />} />
        <Route path="/c/:id" element={<Chat />} />
        <Route path="/money-engine" element={<MoneyEnginePage />} />
        <Route path="/drafts" element={<DraftsQueuePage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/graph" element={<GraphView />} />
        <Route path="/anomaly" element={<AnomalyPage />} />
        <Route path="/tax" element={<TaxPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
