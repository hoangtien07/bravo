// Fetch wrapper: gắn bearer JWT (sessionStorage), xử lý 401 -> về login.

const TOKEN_KEY = "bravo_token";

export const auth = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (t: string) => sessionStorage.setItem(TOKEN_KEY, t),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};

let onUnauthorized: () => void = () => {};
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

export function authHeaders(): Record<string, string> {
  const t = auth.get();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export async function api<T = unknown>(
  path: string,
  opts: RequestInit = {}
): Promise<T> {
  const res = await fetch(path, {
    ...opts,
    headers: { ...authHeaders(), ...(opts.headers || {}) },
  });
  if (res.status === 401) {
    auth.clear();
    onUnauthorized();
    throw new Error("Phiên đăng nhập đã hết hạn");
  }
  if (!res.ok) {
    let detail = `Lỗi ${res.status}`;
    try {
      const j = await res.json();
      detail = j.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function login(username: string, password: string): Promise<void> {
  const body = new URLSearchParams({ username, password });
  const res = await fetch("/api/auth/login", { method: "POST", body });
  if (!res.ok) throw new Error("Đăng nhập thất bại");
  const { access_token } = await res.json();
  auth.set(access_token);
}
