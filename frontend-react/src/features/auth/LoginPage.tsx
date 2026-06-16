import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Input } from "@/components/ui";
import { useAuth } from "@/store/auth";

export function LoginPage() {
  const [email, setEmail] = useState("ketoan@bravo.vn");
  const [pw, setPw] = useState("demo123");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const nav = useNavigate();

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
      </Card>
    </div>
  );
}
