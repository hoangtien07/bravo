import { Component, lazy, Suspense, useEffect, type ErrorInfo, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import SignIn from "./components/SignIn";
import AppShell from "./components/AppShell";
import NewConversation from "./components/NewConversation";
import ActiveConversation from "./components/ActiveConversation";
import FinancialCloseReadiness from "./components/FinancialCloseReadiness";
import AccountingWork from "./components/AccountingWork";
import FinancialCloseGraph from "./components/FinancialCloseGraph";
import DraftApproval from "./components/DraftApproval";
import KnowledgeLibrary from "./components/KnowledgeLibrary";
import Admin from "./components/Admin";
import QAPanel from "./components/QAPanel";
import { AppProvider, useApp, type Screen } from "./context/AppContext";
import { QAProvider, useQA } from "./context/QAContext";
import { ThemeProvider } from "./design/ThemeContext";
import { Banner, EmptyState, ErrorState, PermissionDeniedState, SkeletonBlock, T } from "./components/shared";
import { ConversationHistory, NotFoundPage, ReviewIndex, SafeAlias, SharedConversation } from "./components/PrototypePages";

const MoneyEngine = lazy(() => import("./components/OperationalToolPage").then(module => ({ default: () => <module.default kind="money" /> })));
const Anomaly = lazy(() => import("./components/OperationalToolPage").then(module => ({ default: () => <module.default kind="anomaly" /> })));
const Tax = lazy(() => import("./components/OperationalToolPage").then(module => ({ default: () => <module.default kind="tax" /> })));
const KnowledgeGraph = lazy(() => import("./components/OperationalToolPage").then(module => ({ default: () => <module.default kind="graph" /> })));

const SCREEN_PATH: Record<Screen, string> = {
  "new-conversation": "/",
  "active-conversation": "/c/fixture:current",
  conversations: "/conversations",
  "financial-close": "/financial-close",
  "accounting-work": "/accounting-work",
  "financial-graph": "/financial-close/graph",
  "draft-approval": "/approvals",
  knowledge: "/knowledge",
  admin: "/admin",
  "money-engine": "/tools/money-engine",
  anomaly: "/tools/anomaly",
  tax: "/tools/tax",
  "knowledge-graph": "/tools/knowledge-graph",
  "review-index": "/review",
};

function screenFromPath(pathname: string): Screen {
  if (pathname.startsWith("/c/")) return "active-conversation";
  const match = (Object.entries(SCREEN_PATH) as [Screen, string][]).find(([, path]) => path === pathname);
  return match?.[0] ?? "new-conversation";
}

function ProtectedLayout({ children }: { children: ReactNode }) {
  const { state, dispatch } = useApp();
  const { qa } = useQA();
  const location = useLocation();
  const allowed = state.authenticated || qa.enabled;

  useEffect(() => {
    if (!allowed) return;
    const routeScreen = screenFromPath(location.pathname);
    if (routeScreen !== state.screen) dispatch({ type: "NAVIGATE", screen: routeScreen });
  }, [allowed, dispatch, location.pathname, state.screen]);

  if (!allowed) {
    const next = `${location.pathname}${location.search}${location.hash}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }
  return <><AppShell><QAStateBoundary state={qa.enabled ? qa.componentState : "default"} capability={state.capability}>{children}</QAStateBoundary></AppShell><QAPanel /></>;
}

function LoginRoute() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const rawNext = params.get("next") ?? "/";
  const safeNext = rawNext.startsWith("/") && !rawNext.startsWith("//") && !rawNext.startsWith("/shared/") ? rawNext : "/";
  if (state.authenticated) return <Navigate to={safeNext} replace />;
  return <SignIn onSignIn={() => { dispatch({ type: "SIGN_IN" }); navigate(safeNext, { replace: true }); }} />;
}

function ShellRoute({ children }: { children: ReactNode }) {
  return <ProtectedLayout><RouteErrorBoundary>{children}</RouteErrorBoundary></ProtectedLayout>;
}

class RouteErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(_error: Error, _info: ErrorInfo) { /* Presentation boundary: no remote logging in fixture phase. */ }
  render() {
    if (!this.state.failed) return this.props.children;
    return <ErrorState title="Không thể hiển thị màn hình" body="Tải lại trạng thái fixture hoặc trở về trang bắt đầu. Không có thao tác nào được gửi tới BRAVO ERP." />;
  }
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />
      <Route path="/shared/:token" element={<SharedConversation />} />
      <Route path="/" element={<ShellRoute><NewConversation /></ShellRoute>} />
      <Route path="/c/:id" element={<ShellRoute><ActiveConversation /></ShellRoute>} />
      <Route path="/conversations" element={<ShellRoute><ConversationHistory /></ShellRoute>} />
      <Route path="/financial-close" element={<ShellRoute><FinancialCloseReadiness /></ShellRoute>} />
      <Route path="/accounting-work" element={<ShellRoute><AccountingWork /></ShellRoute>} />
      <Route path="/financial-close/graph" element={<ShellRoute><FinancialCloseGraph /></ShellRoute>} />
      <Route path="/approvals" element={<ShellRoute><DraftApproval /></ShellRoute>} />
      <Route path="/knowledge" element={<ShellRoute><KnowledgeLibrary /></ShellRoute>} />
      <Route path="/admin" element={<ShellRoute><Admin /></ShellRoute>} />
      <Route path="/tools/money-engine" element={<ShellRoute><Suspense fallback={<SkeletonBlock />}><MoneyEngine /></Suspense></ShellRoute>} />
      <Route path="/tools/anomaly" element={<ShellRoute><Suspense fallback={<SkeletonBlock />}><Anomaly /></Suspense></ShellRoute>} />
      <Route path="/tools/tax" element={<ShellRoute><Suspense fallback={<SkeletonBlock />}><Tax /></Suspense></ShellRoute>} />
      <Route path="/tools/knowledge-graph" element={<ShellRoute><Suspense fallback={<SkeletonBlock />}><KnowledgeGraph /></Suspense></ShellRoute>} />
      <Route path="/review" element={<ShellRoute><ReviewIndex /></ShellRoute>} />
      <Route path="/documents" element={<SafeAlias to="/knowledge" />} />
      <Route path="/drafts" element={<SafeAlias to="/approvals" />} />
      <Route path="/money-engine" element={<SafeAlias to="/tools/money-engine" />} />
      <Route path="/anomaly" element={<SafeAlias to="/tools/anomaly" />} />
      <Route path="/tax" element={<SafeAlias to="/tools/tax" />} />
      <Route path="/graph" element={<SafeAlias to="/tools/knowledge-graph" />} />
      <Route path="*" element={<ShellRoute><NotFoundPage /></ShellRoute>} />
    </Routes>
  );
}

function QAStateBoundary({ state, capability, children }: { state: ReturnType<typeof useQA>["qa"]["componentState"]; capability: ReturnType<typeof useApp>["state"]["capability"]; children: ReactNode }) {
  if (state === "loading") return <div style={{ flex: 1, overflow: "auto", padding: 32, background: T.canvas }}><SkeletonBlock /></div>;
  if (state === "empty") return <div style={{ flex: 1, overflow: "auto" }}><EmptyState title="Chưa có dữ liệu trong phạm vi này" body="Chọn phạm vi khác hoặc bắt đầu công việc mới." icon="○" /></div>;
  if (state === "error") return <div style={{ flex: 1, overflow: "auto" }}><ErrorState title="Không thể tải nội dung" body="Thử tải lại. Nếu lỗi tiếp diễn, kiểm tra trạng thái dịch vụ trong khu vực Quản trị." /></div>;
  if (state === "permission_denied") return <PermissionDeniedState message="Vai trò hiện tại không được phép xem nội dung trong phạm vi này." />;
  if (state === "session_expired") return <div style={{ flex: 1, overflow: "auto" }}><ErrorState title="Phiên đã hết hạn" body="Đăng nhập lại để tiếp tục. Nội dung đã nhập được giữ trong phiên mô phỏng này." /></div>;
  const notice = state === "stale" ? <Banner variant="warning"><strong>Bằng chứng đã lỗi thời.</strong> Cần đánh giá lại trước khi sử dụng.</Banner>
    : state === "conflict" || state === "revision_conflict" ? <Banner variant="error"><strong>Phát hiện xung đột.</strong> Không áp dụng thay đổi cho đến khi tải lại và so sánh revision.</Banner>
    : state === "success" ? <Banner variant="success"><strong>Trạng thái minh họa đã hoàn tất.</strong> Không có thay đổi nào được thực hiện trên BRAVO ERP.</Banner>
    : state === "offline" || capability !== "online" ? <Banner variant="warning"><strong>Khả năng đang bị giới hạn.</strong> Không có fallback cloud âm thầm; kết luận thiếu nguồn vẫn chưa xác nhận.</Banner> : null;
  return <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", overflow: "hidden" }}>{notice}{children}</div>;
}

export default function App() {
  return <AppProvider><QAProvider><ThemeProvider><AppRoutes /></ThemeProvider></QAProvider></AppProvider>;
}
