import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import bravoLogo from "../imports/bravo-logo.png";
import { T, useFocusTrap } from "../components/shared";

export function LiveShell({ children }: { children: ReactNode }) {
  const { identity, capabilities, logout } = useAuth();
  const navigate = useNavigate(); const [open, setOpen] = useState(false);
  const opener = useRef<HTMLButtonElement>(null); const drawer = useRef<HTMLDivElement>(null);
  useFocusTrap(drawer, open);
  useEffect(() => { if (!open) opener.current?.focus(); }, [open]);
  useEffect(() => {
    if (!open) return;
    const escape = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", escape); return () => window.removeEventListener("keydown", escape);
  }, [open]);
  const nav = (closeOnNavigate = false) => <nav aria-label="Điều hướng sản phẩm" style={{ display: "grid", gap: 4 }}>
    <NavLink end to="/" onClick={() => closeOnNavigate && setOpen(false)} style={linkStyle}>Knowledge Chat</NavLink>
    <NavLink to="/conversations" onClick={() => closeOnNavigate && setOpen(false)} style={linkStyle}>Hội thoại gần đây</NavLink>
    {capabilities.read && <NavLink to="/work" onClick={() => closeOnNavigate && setOpen(false)} style={linkStyle}>Công việc AI</NavLink>}
  </nav>;
  return <div style={{ minHeight: "100vh", background: T.canvas, color: T.strong }}>
    <a href="#main" className="live-shell-skip">Bỏ qua điều hướng</a>
    <header className="live-shell-header" style={{ height: 60, background: T.white, borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", padding: "0 18px", gap: 12 }}>
      <button ref={opener} onClick={() => setOpen(true)} aria-label="Mở điều hướng" style={menuButton}>☰</button>
      <Link to="/" style={{ display: "inline-flex", alignItems: "center", gap: 8, color: T.strong, textDecoration: "none", fontWeight: 700 }}><img src={bravoLogo} alt="BRAVO" style={{ height: 24 }} /> Accounting Intelligence</Link>
      <div style={{ flex: 1 }} />
      <span className="live-shell-identity" style={{ fontSize: 12, color: T.secondary }}>{identity?.fullName ?? "Phiên đã xác thực"}</span>
      <button onClick={() => { logout(); navigate("/login"); }} style={logoutStyle}>Đăng xuất</button>
    </header>
    <div className="live-shell-body" style={{ display: "grid", gridTemplateColumns: "230px minmax(0, 1fr)", minHeight: "calc(100vh - 60px)" }}>
      <aside className="live-shell-desktop-nav" style={{ background: T.white, borderRight: `1px solid ${T.border}`, padding: 14 }}>
        <p style={{ color: T.secondary, fontSize: 12, margin: "0 0 10px" }}>MODULE ĐƯỢC CẤP QUYỀN</p>{nav()}
        <div style={{ borderTop: `1px solid ${T.border}`, marginTop: 18, paddingTop: 12, color: T.secondary, fontSize: 12 }}>Phạm vi: Chưa xác định từ máy chủ</div>
      </aside>
      <main id="main" style={{ minWidth: 0, display: "flex" }}>{children}</main>
    </div>
    {open && <div role="dialog" aria-modal="true" aria-label="Điều hướng" className="live-shell-backdrop" onMouseDown={() => setOpen(false)}>
      <div ref={drawer} onMouseDown={event => event.stopPropagation()} style={{ width: 280, height: "100%", background: T.white, padding: 18, boxShadow: "4px 0 20px rgba(0,0,0,.2)" }}>
        <button onClick={() => setOpen(false)} style={logoutStyle}>Đóng</button><div style={{ marginTop: 20 }}>{nav(true)}</div>
      </div>
    </div>}
  </div>;
}

const linkStyle = ({ isActive }: { isActive: boolean }): CSSProperties => ({ minHeight: 42, display: "flex", alignItems: "center", padding: "0 10px", textDecoration: "none", borderRadius: 5, color: isActive ? T.interactive : T.strong, background: isActive ? T.softTeal : "transparent", fontWeight: isActive ? 700 : 500 });
const menuButton: CSSProperties = { minHeight: 44, minWidth: 44, border: 0, background: "transparent", cursor: "pointer", fontSize: 20, color: T.strong };
const logoutStyle: CSSProperties = { minHeight: 36, border: `1px solid ${T.border}`, borderRadius: 5, background: T.white, color: T.secondary, cursor: "pointer", padding: "0 10px" };
