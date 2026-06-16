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
  $("apCard").style.display = "block";
  $("draftsCard").style.display = "block";
  loadDrafts();
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

// ---------- AP money-engine: hoá đơn -> bút toán nháp ----------
const fmtMoney = (s) => {
  const n = Number(s);
  return isNaN(n) ? escapeHtml(String(s)) : n.toLocaleString("vi-VN");
};

function renderJournal(je) {
  if (!je || !je.lines) return `<pre>${escapeHtml(JSON.stringify(je, null, 1))}</pre>`;
  const rows = je.lines.map((l) => {
    const isDebit = Number(l.debit) > 0;
    const amt = isDebit ? l.debit : l.credit;
    return `<tr>
      <td>${isDebit ? "Nợ " + escapeHtml(l.account) : ""}</td>
      <td>${!isDebit ? "Có " + escapeHtml(l.account) : ""}</td>
      <td>${escapeHtml(l.memo || "")}</td>
      <td class="num">${fmtMoney(amt)}</td>
      <td class="muted">${escapeHtml(l.source_ref || "")}</td>
    </tr>`;
  }).join("");
  const balanced = je.total_debit === je.total_credit;
  const inv = je.invoice || {};
  const flags = (je.validation_flags || []).map((f) => `<div class="cite refuse">⚠ ${escapeHtml(f)}</div>`).join("");
  return `<div class="muted">HĐ ${escapeHtml(inv.ky_hieu || "")}-${escapeHtml(inv.so_hoa_don || "")}
      · NCC MST ${escapeHtml(inv.mst_ban || "")}</div>
    <table class="je"><thead><tr><th>Nợ</th><th>Có</th><th>Diễn giải</th><th class="num">Số tiền</th><th>Nguồn</th></tr></thead>
      <tbody>${rows}</tbody>
      <tfoot><tr><td colspan="3"><b>Tổng</b></td><td class="num"><b>${fmtMoney(je.total_debit)}</b></td><td></td></tr></tfoot>
    </table>
    <span class="badge ${balanced ? "ok" : "warn"}">${balanced ? "✓ cân Nợ=Có" : "✗ KHÔNG cân"}</span>
    <span class="badge ${je.needs_review ? "warn" : "ok"}">${je.needs_review ? "⚠ cần kế toán xem" : "✓ tự động"}</span>
    ${flags}`;
}

async function uploadInvoice() {
  const f = $("invFile").files[0];
  if (!f) { $("invResult").innerHTML = `<p class="refuse">Chọn file hoá đơn XML trước.</p>`; return; }
  $("invResult").innerHTML = `<p class="muted">Đang xử lý hoá đơn…</p>`;
  const fd = new FormData();
  fd.append("file", f);
  try {
    const r = await fetch(`${API}/api/invoices/draft`, { method: "POST", headers: auth(), body: fd });
    const d = await r.json();
    if (!r.ok) { $("invResult").innerHTML = `<p class="refuse">Lỗi ${r.status}: ${escapeHtml(d.detail || "")}</p>`; return; }
    $("invResult").innerHTML = `<p class="muted">Đã tạo bút toán nháp (id ${d.draft_id.slice(0, 8)}…):</p>`
      + renderJournal(d.journal);
    loadDrafts();
  } catch (e) { $("invResult").innerHTML = `<p class="refuse">Lỗi mạng: ${escapeHtml(String(e))}</p>`; }
}

async function loadDrafts() {
  const box = $("draftsList");
  box.innerHTML = `<p class="muted">Đang tải…</p>`;
  try {
    const r = await fetch(`${API}/api/drafts`, { headers: auth() });
    if (!r.ok) { box.innerHTML = `<p class="refuse">Không tải được nháp (lỗi ${r.status}).</p>`; return; }
    const drafts = await r.json();
    if (!drafts.length) { box.innerHTML = `<p class="muted">Không có nháp nào chờ duyệt.</p>`; return; }
    box.innerHTML = drafts.map((d) => `<div class="draft">
      ${d.kind === "journal_entry" ? renderJournal(d.payload) : `<pre>${escapeHtml(JSON.stringify(d.payload, null, 1))}</pre>`}
      <div class="row" style="margin-top:8px">
        <button class="btn-sm" onclick="approveDraft('${d.id}')">Duyệt</button>
        <button class="btn-sm btn-rose" onclick="rejectDraft('${d.id}')">Từ chối</button>
        <span class="muted">id ${d.id.slice(0, 8)}…</span>
      </div></div>`).join("");
  } catch (e) { box.innerHTML = `<p class="refuse">Lỗi mạng: ${escapeHtml(String(e))}</p>`; }
}

async function approveDraft(id) {
  const r = await fetch(`${API}/api/drafts/${id}/approve`, { method: "POST", headers: auth() });
  if (r.status === 403) { alert("Maker-checker: không được tự duyệt nháp của chính mình. Cần người khác duyệt."); return; }
  if (!r.ok) { const d = await r.json().catch(() => ({})); alert(`Không duyệt được (lỗi ${r.status}): ${d.detail || ""}`); return; }
  loadDrafts();
}

async function rejectDraft(id) {
  const reason = prompt("Lý do từ chối?", "Sai tài khoản / cần sửa");
  if (reason === null) return;
  const r = await fetch(`${API}/api/drafts/${id}/reject`, {
    method: "POST", headers: { ...auth(), "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
  if (!r.ok) { alert(`Không từ chối được (lỗi ${r.status}).`); return; }
  loadDrafts();
}

$("loginBtn").onclick = login;
$("askBtn").onclick = ask;
$("invBtn").onclick = uploadInvoice;
$("reloadDrafts").onclick = loadDrafts;
