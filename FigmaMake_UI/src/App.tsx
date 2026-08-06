import { Component, type ErrorInfo, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import SignIn from "./components/SignIn";
import AccountingWork from "./components/AccountingWork";
import { AccountingCaseWorkspace, NewAccountingCase } from "./accounting-work/CaseScreens";
import { AppProvider } from "./context/AppContext";
import { QAProvider, useQA } from "./context/QAContext";
import { ThemeProvider } from "./design/ThemeContext";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { ErrorState } from "./components/shared";
import { LiveShell } from "./app/LiveShell";
import { ConversationHistory, ConversationHome, ConversationWorkspace, SharedConversationPage } from "./conversation/ConversationPages";
import { ReviewIndex } from "./components/PrototypePages";

function LoginRoute() { const auth = useAuth(); const location = useLocation(); const next = new URLSearchParams(location.search).get("next") ?? "/"; const safeNext = next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/shared/") ? next : "/"; if (auth.status === "authenticated") return <Navigate to={safeNext} replace />; return <SignIn loadingOidc={false} oidcEnabled={auth.oidcEnabled} authError={auth.error} onPasswordSignIn={auth.signInWithPassword} onOidcSignIn={() => auth.beginOidc(safeNext)} />; }
function Protected({ children }: { children: ReactNode }) { const auth = useAuth(); const location = useLocation(); if (auth.status === "checking") return <div aria-live="polite">Đang xác minh phiên đăng nhập…</div>; if (auth.status === "unavailable") return <ErrorState title="Không thể xác minh phiên" body={auth.error ?? "Kiểm tra kết nối rồi thử lại."} />; if (auth.status !== "authenticated") return <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />; return <LiveShell><Boundary>{children}</Boundary></LiveShell>; }
class Boundary extends Component<{ children: ReactNode }, { failed: boolean }> { state = { failed: false }; static getDerivedStateFromError() { return { failed: true }; } componentDidCatch(_error: Error, _info: ErrorInfo) {} render() { return this.state.failed ? <ErrorState title="Không thể hiển thị màn hình" body="Tải lại hoặc quay về trang bắt đầu. Không có thao tác nào được gửi đến BRAVO ERP." /> : this.props.children; } }
function NormalRoutes() { return <Routes><Route path="/login" element={<LoginRoute />} /><Route path="/shared/:token" element={<SharedConversationPage />} /><Route path="/" element={<Protected><ConversationHome /></Protected>} /><Route path="/c/:conversationId" element={<Protected><ConversationWorkspace /></Protected>} /><Route path="/conversations" element={<Protected><ConversationHistory /></Protected>} /><Route path="/work" element={<Protected><AccountingWork /></Protected>} /><Route path="/work/new/:caseType" element={<Protected><NewAccountingCase /></Protected>} /><Route path="/work/cases/:caseId" element={<Protected><AccountingCaseWorkspace /></Protected>} /><Route path="/work/cases/:caseId/findings/:findingId" element={<Protected><AccountingCaseWorkspace /></Protected>} /><Route path="/financial-close" element={<Navigate to="/work/new/period_close_readiness" replace />} /><Route path="/accounting-work" element={<Navigate to="/work" replace />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes>; }
function RoutesForMode() { const { qa } = useQA(); return qa.enabled ? <Routes><Route path="/review" element={<ReviewIndex />} /><Route path="/work" element={<AccountingWork />} /><Route path="*" element={<Navigate to="/review?qa=1" replace />} /></Routes> : <NormalRoutes />; }
export default function App() { return <AppProvider><QAProvider><AuthProvider><ThemeProvider><RoutesForMode /></ThemeProvider></AuthProvider></QAProvider></AppProvider>; }
