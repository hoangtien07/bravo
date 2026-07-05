import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, KeyRound, Plus, Shield, UserPlus } from "lucide-react";
import { api } from "@/api/client";
import { Badge, Button, Card, Input } from "@/components/ui";
import { useAuth } from "@/store/auth";

interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  is_admin: boolean;
  permissions: string[];
  department_ids: string[];
}
interface Dept { id: string; name: string; sensitive: boolean; }
interface UsageRow { employee_id: string; email: string | null; turns: number; tokens: number; est_cost: number; }

// Quản trị tối thiểu (W1.8): tạo user + phòng ban + reset mật khẩu — không cần chạy script.
export function AdminPage() {
  const { identity } = useAuth();
  const nav = useNavigate();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [depts, setDepts] = useState<Dept[]>([]);
  const [perms, setPerms] = useState<string[]>([]);
  const [usage, setUsage] = useState<UsageRow[]>([]);
  const [msg, setMsg] = useState<string | null>(null);

  // form tạo user
  const [nu, setNu] = useState({ email: "", full_name: "", password: "", is_admin: false,
    permissions: [] as string[], department_ids: [] as string[] });
  const [newDept, setNewDept] = useState("");

  const load = () => {
    api<AdminUser[]>("/api/admin/users").then(setUsers).catch((e) => setMsg(String(e)));
    api<Dept[]>("/api/admin/departments").then(setDepts).catch(() => {});
    api<string[]>("/api/admin/permissions").then(setPerms).catch(() => {});
    api<UsageRow[]>("/api/admin/usage?days=7").then(setUsage).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  if (identity && !identity.is_admin) {
    return <div className="p-6 text-sm text-muted-foreground">Chỉ quản trị viên mới truy cập trang này.</div>;
  }

  const createUser = async () => {
    try {
      await api("/api/admin/users", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(nu),
      });
      setMsg(`Đã tạo ${nu.email}`);
      setNu({ email: "", full_name: "", password: "", is_admin: false, permissions: [], department_ids: [] });
      load();
    } catch (e) { setMsg(e instanceof Error ? e.message : "Lỗi tạo user"); }
  };

  const createDept = async () => {
    if (!newDept.trim()) return;
    try {
      await api("/api/admin/departments", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newDept.trim() }),
      });
      setNewDept(""); load();
    } catch (e) { setMsg(e instanceof Error ? e.message : "Lỗi tạo phòng ban"); }
  };

  const resetPw = async (u: AdminUser) => {
    const pw = prompt(`Đặt mật khẩu mới cho ${u.email} (≥6 ký tự):`);
    if (!pw) return;
    try {
      await api(`/api/admin/users/${u.id}/password`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_password: pw }),
      });
      setMsg(`Đã đặt lại mật khẩu cho ${u.email}`);
    } catch (e) { setMsg(e instanceof Error ? e.message : "Lỗi"); }
  };

  const togglePerm = (p: string) =>
    setNu((s) => ({ ...s, permissions: s.permissions.includes(p)
      ? s.permissions.filter((x) => x !== p) : [...s.permissions, p] }));
  const toggleDept = (id: string) =>
    setNu((s) => ({ ...s, department_ids: s.department_ids.includes(id)
      ? s.department_ids.filter((x) => x !== id) : [...s.department_ids, id] }));
  const deptName = (id: string) => depts.find((d) => d.id === id)?.name || id.slice(0, 8);

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="flex items-center gap-2 border-b border-border px-4 py-2">
        <Button variant="ghost" size="icon" onClick={() => nav("/")} aria-label="quay lại"><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="font-semibold tracking-tight flex items-center gap-2"><Shield className="h-4 w-4" /> Quản trị</h1>
      </header>

      <div className="mx-auto max-w-3xl p-4 space-y-4">
        {msg && <div className="text-xs text-muted-foreground rounded-md bg-muted/40 px-3 py-2">{msg}</div>}

        {/* Tạo phòng ban */}
        <Card className="p-4">
          <h2 className="font-medium mb-2">Phòng ban</h2>
          <div className="flex items-center gap-2">
            <Input value={newDept} onChange={(e) => setNewDept(e.target.value)} placeholder="Tên phòng ban mới" />
            <Button size="sm" onClick={createDept}><Plus className="h-4 w-4" /> Thêm</Button>
          </div>
          <div className="flex flex-wrap gap-1 mt-2">
            {depts.map((d) => <Badge key={d.id} tone={d.sensitive ? "warn" : "muted"}>{d.name}</Badge>)}
          </div>
        </Card>

        {/* Tạo user */}
        <Card className="p-4 space-y-2">
          <h2 className="font-medium flex items-center gap-2"><UserPlus className="h-4 w-4" /> Tạo người dùng</h2>
          <div className="grid grid-cols-2 gap-2">
            <Input value={nu.email} onChange={(e) => setNu({ ...nu, email: e.target.value })} placeholder="email" />
            <Input value={nu.full_name} onChange={(e) => setNu({ ...nu, full_name: e.target.value })} placeholder="họ tên" />
            <Input type="password" value={nu.password} onChange={(e) => setNu({ ...nu, password: e.target.value })} placeholder="mật khẩu (≥6)" />
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={nu.is_admin} onChange={(e) => setNu({ ...nu, is_admin: e.target.checked })} className="accent-primary" />
              Quản trị viên
            </label>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Phòng ban (RLS scope)</div>
            <div className="flex flex-wrap gap-1">
              {depts.map((d) => (
                <button key={d.id} onClick={() => toggleDept(d.id)}
                        className={`rounded-md px-2 py-0.5 text-xs border ${nu.department_ids.includes(d.id) ? "bg-primary text-primary-foreground border-primary" : "border-border hover:bg-muted"}`}>
                  {d.name}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Quyền</div>
            <div className="flex flex-wrap gap-1">
              {perms.map((p) => (
                <button key={p} onClick={() => togglePerm(p)}
                        className={`rounded-md px-2 py-0.5 text-xs border font-mono ${nu.permissions.includes(p) ? "bg-primary text-primary-foreground border-primary" : "border-border hover:bg-muted"}`}>
                  {p}
                </button>
              ))}
            </div>
          </div>
          <Button size="sm" onClick={createUser} disabled={!nu.email || !nu.full_name || nu.password.length < 6}>
            <UserPlus className="h-4 w-4" /> Tạo
          </Button>
        </Card>

        {/* Usage / chi phí (W2.4) — token THẬT 7 ngày */}
        {usage.length > 0 && (
          <Card className="p-0 overflow-hidden">
            <div className="px-3 py-2 text-sm font-medium border-b border-border">Token & chi phí (7 ngày)</div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="px-3 py-2">Người dùng</th><th className="text-right">Lượt</th>
                  <th className="text-right">Token</th><th className="text-right pr-3">Ước phí</th>
                </tr>
              </thead>
              <tbody>
                {usage.map((u) => (
                  <tr key={u.employee_id} className="border-b border-border">
                    <td className="px-3 py-1.5">{u.email || u.employee_id.slice(0, 8)}</td>
                    <td className="text-right tabular">{u.turns}</td>
                    <td className="text-right tabular">{u.tokens.toLocaleString("vi-VN")}</td>
                    <td className="text-right tabular pr-3">{u.est_cost.toLocaleString("vi-VN", { maximumFractionDigits: 4 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        {/* Danh sách user */}
        <Card className="p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted-foreground border-b border-border">
                <th className="px-3 py-2">Email</th><th>Họ tên</th><th>Phòng ban</th><th>Quyền</th><th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-border align-top">
                  <td className="px-3 py-2">{u.email}{u.is_admin && <Badge tone="primary" className="ml-1">admin</Badge>}</td>
                  <td className="py-2">{u.full_name}</td>
                  <td className="py-2 text-xs">{u.department_ids.map(deptName).join(", ") || "—"}</td>
                  <td className="py-2 text-xs font-mono">{u.permissions.join(", ") || "—"}</td>
                  <td className="py-2 pr-2 text-right">
                    <button onClick={() => resetPw(u)} className="text-xs text-primary hover:underline inline-flex items-center gap-1">
                      <KeyRound className="h-3 w-3" /> Đặt mật khẩu
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  );
}
