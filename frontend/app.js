// Minimal BRAVO AI Copilot frontend — login + ask + citations. No build step.
const API = "";
let token = null;

const $ = (id) => document.getElementById(id);

async function login() {
  const body = new URLSearchParams({ username: $("email").value, password: $("password").value });
  const r = await fetch(`${API}/api/auth/login`, { method: "POST", body });
  if (!r.ok) { $("who").textContent = "Đăng nhập thất bại."; return; }
  token = (await r.json()).access_token;
  const me = await (await fetch(`${API}/api/me`, { headers: auth() })).json();
  $("who").textContent = `Xin chào ${me.full_name} — phòng ban: ${me.department_ids.length} · admin: ${me.is_admin}`;
  $("askCard").style.display = "block";
}

const auth = () => ({ Authorization: `Bearer ${token}` });

async function ask() {
  const q = $("q").value.trim();
  if (!q) return;
  $("answer").innerHTML = '<p class="muted">Đang hỏi…</p>';
  const r = await fetch(`${API}/api/ask`, {
    method: "POST",
    headers: { ...auth(), "Content-Type": "application/json" },
    body: JSON.stringify({ question: q }),
  });
  if (!r.ok) { $("answer").innerHTML = `<p class="refuse">Lỗi ${r.status}</p>`; return; }
  const d = await r.json();
  const cites = (d.citations || []).map((c, i) => {
    const loc = [c.page_number && `trang ${c.page_number}`, c.sheet_name && `sheet ${c.sheet_name}`,
      c.cell_range && `ô ${c.cell_range}`].filter(Boolean).join(", ");
    return `<div class="cite">[${i + 1}] nguồn ${c.source_id}${loc ? " · " + loc : ""}</div>`;
  }).join("");
  $("answer").innerHTML = `<pre class="${d.grounded ? "" : "refuse"}">${escapeHtml(d.answer)}</pre>`
    + (d.grounded ? `<p class="muted">Dẫn chứng:</p>${cites}` : "");
}

function escapeHtml(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

$("loginBtn").onclick = login;
$("askBtn").onclick = ask;
