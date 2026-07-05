import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, auth as tokenStore } from "@/api/client";
import { Button, Card, Input } from "@/components/ui";
import { useAuth } from "@/store/auth";

// Prefill CHỈ khi build demo bật cờ (VITE_DEMO_LOGIN=email:password). Bản production
// build không có cờ này -> ô trống, bundle không chứa credential.
const _demo = (import.meta.env.VITE_DEMO_LOGIN ?? "").split(":");
const DEMO_EMAIL = _demo[0] ?? "";
const DEMO_PW = _demo[1] ?? "";

export function LoginPage() {
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [pw, setPw] = useState(DEMO_PW);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [oidc, setOidc] = useState(false);
  const { login, loadMe } = useAuth();
  const nav = useNavigate();

  // OIDC callback redirect về /login#token=<jwt> -> lưu token + vào app (W2.1).
  useEffect(() => {
    const m = window.location.hash.match(/token=([^&]+)/);
    if (m) {
      tokenStore.set(decodeURIComponent(m[1]));
      window.location.hash = "";
      loadMe().then(() => nav("/"));
      return;
    }
    api<{ oidc_enabled: boolean }>("/api/auth/config")
      .then((c) => setOidc(c.oidc_enabled)).catch(() => {});
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      await login(email, pw);
      nav("/");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Đăng nhập thất bại");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center p-4">
      <Card className="w-full max-w-sm p-6">
        <h1 className="text-xl font-bold tracking-tight">BRAVO AI Copilot</h1>
        <p className="text-sm text-muted-foreground mb-4">Đăng nhập để bắt đầu hội thoại.</p>
        <form onSubmit={submit} className="space-y-3">
          <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" aria-label="email" />
          <Input type="password" value={pw} onChange={(e) => setPw(e.target.value)} placeholder="mật khẩu" aria-label="mật khẩu" />
          {err && <p className="text-sm text-destructive">{err}</p>}
          <Button type="submit" className="w-full" disabled={busy}>{busy ? "Đang đăng nhập…" : "Đăng nhập"}</Button>
        </form>
        {oidc && (
          <a href="/api/auth/oidc/login"
             className="mt-3 block text-center rounded-md border border-border px-4 py-2 text-sm hover:bg-muted">
            Đăng nhập bằng SSO (AD/LDAP)
          </a>
        )}
      </Card>
    </div>
  );
}
