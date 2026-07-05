import { useEffect } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { setUnauthorizedHandler } from "@/api/client";
import { useAuth } from "@/store/auth";
import { AppShell } from "@/features/chat/AppShell";
import { ChatView } from "@/features/chat/ChatView";
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
  if (!identity && !loading) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  const { identity, loadMe } = useAuth();
  const nav = useNavigate();

  useEffect(() => {
    setUnauthorizedHandler(() => nav("/login"));
    loadMe();
  }, []);

  return (
    <Routes>
      <Route path="/login" element={identity ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/shared/:token" element={<SharedPage />} />
      <Route element={<Protected><AppShell /></Protected>}>
        <Route path="/" element={<ChatView />} />
        <Route path="/c/:id" element={<ChatView />} />
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
