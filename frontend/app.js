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

// Citations differ by endpoint: /ask returns structured objects; /agent/ask returns
// pre-formatted strings (the loop's own c.citation()). Normalize both to an HTML block.
function renderCites(citations) {
  return (citations || []).map((c, i) => {
    let text;
    if (typeof c === "string") {
      text = c;
    } else {
      const loc = [c.page_number && `trang ${c.page_number}`, c.sheet_name && `sheet ${c.sheet_name}`,
        c.cell_range && `ô ${c.cell_range}`].filter(Boolean).join(", ");
      text = `nguồn ${c.source_id}${loc ? " · " + loc : ""}`;
    }
    return `<div class="cite">[${i + 1}] ${escapeHtml(text)}</div>`;
  }).join("");
}

async function ask() {
  const q = $("q").value.trim();
  if (!q) return;
  const agentic = $("agentic").checked;
  $("answer").innerHTML = `<p class="muted">Đang hỏi…${agentic ? " (agentic)" : ""}</p>`;
  const path = agentic ? "/api/agent/ask" : "/api/ask";
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { ...auth(), "Content-Type": "application/json" },
    body: JSON.stringify({ question: q }),
  });
  if (!r.ok) { $("answer").innerHTML = `<p class="refuse">Lỗi ${r.status}</p>`; return; }
  const d = await r.json();
  const cites = renderCites(d.citations);
  const badges = agentic
    ? `<p class="muted">`
      + `${d.clarify ? "❓ cần làm rõ · " : ""}`
      + `${d.stopped ? "⛔ dừng: " + escapeHtml(d.stopped) + " · " : ""}`
      + `${d.routed_cloud ? "☁ cloud (đã audit)" : "🔒 local"} · `
      + `${d.grounded ? "✓ đã kiểm chứng số" : "⚠ chưa căn cứ / số đã ẩn"}</p>`
    : "";
  $("answer").innerHTML = `<pre class="${d.grounded ? "" : "refuse"}">${escapeHtml(d.answer)}</pre>`
    + badges + (cites ? `<p class="muted">Dẫn chứng:</p>${cites}` : "");
}

function escapeHtml(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

$("loginBtn").onclick = login;
$("askBtn").onclick = ask;
