/* Darvin CRM — single-page app. Hash routing, token auth, live DRF backend. */
"use strict";

// ── API client ───────────────────────────────────────────────
const API = {
  token: localStorage.getItem("darvin_token"),
  user: JSON.parse(localStorage.getItem("darvin_user") || "null"),
  async req(path, opts = {}) {
    const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
    if (this.token) headers.Authorization = `Token ${this.token}`;
    const res = await fetch(`/api${path}`, { ...opts, headers });
    if (res.status === 401) { this.logout(); throw new Error("Signed out"); }
    if (!res.ok) throw new Error((await res.text()).slice(0, 200));
    return res.status === 204 ? null : res.json();
  },
  get: (p) => API.req(p),
  post: (p, body) => API.req(p, { method: "POST", body: JSON.stringify(body) }),
  patch: (p, body) => API.req(p, { method: "PATCH", body: JSON.stringify(body) }),
  async login(username, password) {
    const data = await this.req("/auth/login/", { method: "POST", body: JSON.stringify({ username, password }) });
    this.token = data.token; this.user = data.user;
    localStorage.setItem("darvin_token", data.token);
    localStorage.setItem("darvin_user", JSON.stringify(data.user));
  },
  logout() {
    this.token = null; this.user = null;
    localStorage.removeItem("darvin_token"); localStorage.removeItem("darvin_user");
    location.hash = "#/login"; render();
  },
};

// ── Helpers ──────────────────────────────────────────────────
const root = document.getElementById("root");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const inr = (v) => {
  v = Number(v);
  if (v >= 1e7) return `₹${(v / 1e7).toFixed(2)}Cr`;
  if (v >= 1e5) return `₹${(v / 1e5).toFixed(1)}L`;
  return `₹${v.toLocaleString("en-IN")}`;
};
const ago = (iso) => {
  if (!iso) return "—";
  const d = (Date.now() - new Date(iso)) / 1000;
  if (d < 3600) return `${Math.max(1, Math.round(d / 60))}m ago`;
  if (d < 86400) return `${Math.round(d / 3600)}h ago`;
  if (d < 604800) return `${Math.round(d / 86400)}d ago`;
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
};
const initials = (name) => (name || "?").split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
const AV_CLASSES = ["deep", "", "green", "olive"];
const avc = (name) => AV_CLASSES[(name || "").length % 4];
const STAGE_TAG = { lead: "olive", prospect: "", customer: "green" };

function toast(msg) {
  document.querySelector(".toast")?.remove();
  const t = document.createElement("div");
  t.className = "toast"; t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2600);
}

// ── Shell ────────────────────────────────────────────────────
const NAV = [
  ["Work", [["#/tasks", "Inbox & Today", "today"]]],
  ["Objects", [["#/contacts", "Contacts", "contacts"], ["#/deals", "Deals", "deals"], ["#/tasks", "Tasks", "tasks"]]],
  ["Insights", [["#/reports", "Reports", "reports"], ["#/automations", "Automations", "automations"]]],
];

function shell(active, crumbs, body) {
  const nav = NAV.map(([label, items]) => `
    <nav class="nav-group"><div class="nav-label">${label}</div>
      ${items.map(([href, name, id]) => `<a class="nav-item ${active === id ? "active" : ""}" href="${href}">${name}</a>`).join("")}
    </nav>`).join("");
  return `
  <div class="app">
    <aside class="sidebar">
      <div class="workspace"><span class="avatar deep">DV</span>
        <div><strong>Darvin</strong><span>workspace · self-hosted</span></div></div>
      ${nav}
      <div class="sidebar-foot">
        <span class="avatar">${initials(API.user ? `${API.user.first_name} ${API.user.last_name}` : API.user?.username)}</span>
        <span style="font-size:13px">${esc(API.user?.first_name || API.user?.username || "")} ${esc(API.user?.last_name || "")}</span>
        <span class="hint"><a href="#" id="logout" style="font-size:12px">Sign out</a></span>
      </div>
    </aside>
    <div class="main">
      <div class="topbar">
        <div class="search-pill" data-cmdk>Search anything… <kbd>⌘K</kbd></div>
        <div class="breadcrumbs">${crumbs}</div>
        <div class="topbar-right"><span class="avatar">${initials(API.user?.username)}</span></div>
      </div>
      <main class="content">${body}</main>
    </div>
  </div>
  <div class="overlay" id="cmdk-overlay"><div class="cmdk">
    <input id="cmdk-input" placeholder="Type a command or search contacts…">
    <div id="cmdk-results"><div class="cmdk-group"><div class="cmdk-label">Go to</div>
      <div class="cmdk-item" data-go="#/contacts">Contacts <span class="hint">G C</span></div>
      <div class="cmdk-item" data-go="#/deals">Deals <span class="hint">G D</span></div>
      <div class="cmdk-item" data-go="#/tasks">Tasks <span class="hint">G T</span></div>
      <div class="cmdk-item" data-go="#/reports">Reports <span class="hint">G R</span></div>
    </div></div>
    <div class="cmdk-foot"><span>⏎ select</span><span>esc close</span></div>
  </div></div>`;
}

function wireShell() {
  document.getElementById("logout")?.addEventListener("click", (e) => { e.preventDefault(); API.logout(); });
  const overlay = document.getElementById("cmdk-overlay");
  document.querySelectorAll("[data-cmdk]").forEach((el) =>
    el.addEventListener("click", () => { overlay.classList.add("open"); overlay.querySelector("input").focus(); }));
  overlay?.addEventListener("click", (e) => { if (e.target === overlay) overlay.classList.remove("open"); });
  overlay?.querySelectorAll("[data-go]").forEach((el) =>
    el.addEventListener("click", () => { overlay.classList.remove("open"); location.hash = el.dataset.go; }));
  const input = document.getElementById("cmdk-input");
  let timer;
  input?.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const q = input.value.trim();
      if (!q) return;
      const data = await API.get(`/contacts/?search=${encodeURIComponent(q)}`);
      document.getElementById("cmdk-results").innerHTML = `<div class="cmdk-group">
        <div class="cmdk-label">Contacts</div>
        ${(data.results || []).slice(0, 6).map((c) => `
          <div class="cmdk-item" data-go="#/contacts/${c.id}">
            <span class="avatar ${avc(c.name)}">${initials(c.name)}</span> ${esc(c.name)}
            <span class="hint">${esc(c.company_name || "")}</span></div>`).join("") || '<div class="cmdk-item">No matches</div>'}
      </div>`;
      document.querySelectorAll("#cmdk-results [data-go]").forEach((el) =>
        el.addEventListener("click", () => { overlay.classList.remove("open"); location.hash = el.dataset.go; }));
    }, 250);
  });
}

let pendingG = false;
document.addEventListener("keydown", (e) => {
  const overlay = document.getElementById("cmdk-overlay");
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault(); overlay?.classList.toggle("open");
    if (overlay?.classList.contains("open")) overlay.querySelector("input").focus();
    return;
  }
  if (e.key === "Escape") { overlay?.classList.remove("open"); document.querySelector(".modal-overlay")?.remove(); return; }
  if (e.target.matches("input, textarea, select")) return;
  if (pendingG) {
    pendingG = false;
    const r = { c: "#/contacts", d: "#/deals", t: "#/tasks", r: "#/reports", a: "#/automations" }[e.key.toLowerCase()];
    if (r) location.hash = r;
    return;
  }
  if (e.key.toLowerCase() === "g") { pendingG = true; setTimeout(() => (pendingG = false), 1200); }
  if (e.key === "/") { e.preventDefault(); document.querySelector(".filter-bar .input")?.focus(); }
});

function modal(html, onMount) {
  document.querySelector(".modal-overlay")?.remove();
  const o = document.createElement("div");
  o.className = "overlay open modal-overlay";
  o.innerHTML = `<div class="modal-card">${html}</div>`;
  o.addEventListener("click", (e) => { if (e.target === o) o.remove(); });
  document.body.appendChild(o);
  onMount?.(o);
}

// ── Views ────────────────────────────────────────────────────

function loginView() {
  root.innerHTML = `
  <div class="login-wrap">
    <div class="login-brand"><span class="logo">Darvin</span>
      <h1>The workshop,<br>not the showroom.</h1>
      <div class="foot">Darvin CRM · self-hosted · made for operators</div></div>
    <div class="login-form"><div class="form-card">
      <h2 class="serif" style="font-size:28px;font-weight:300">Welcome back.</h2>
      <p class="muted" style="margin:4px 0 24px">Sign in to your workspace.</p>
      <form id="login-form">
        <div class="field" style="margin-bottom:14px"><label>Username</label><input class="input" name="username" value="admin" autocomplete="username"></div>
        <div class="field" style="margin-bottom:20px"><label>Password</label><input class="input" type="password" name="password" placeholder="darvin2026" autocomplete="current-password"></div>
        <button class="btn btn-primary" style="width:100%;justify-content:center">Sign in</button>
        <div class="error-note" id="login-err"></div>
        <p class="meta" style="margin-top:20px">Demo: admin / ravi / nisha — password darvin2026</p>
      </form>
    </div></div>
  </div>`;
  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = new FormData(e.target);
    try {
      await API.login(f.get("username"), f.get("password"));
      location.hash = "#/contacts"; render();
    } catch {
      document.getElementById("login-err").textContent = "Invalid credentials.";
    }
  });
}

async function contactsView(params) {
  const q = params.get("search") || "";
  const stage = params.get("stage") || "";
  const data = await API.get(`/contacts/?search=${encodeURIComponent(q)}${stage ? `&stage=${stage}` : ""}`);
  const rows = (data.results || []).map((c) => `
    <tr data-go="#/contacts/${c.id}">
      <td><span class="flex"><span class="avatar ${avc(c.name)}">${initials(c.name)}</span><span class="name">${esc(c.name)}</span></span></td>
      <td>${esc(c.company_name || "—")}</td><td class="muted">${esc(c.role || "—")}</td>
      <td><span class="tag ${STAGE_TAG[c.stage] || ""}">${esc(c.stage)}</span></td>
      <td>${esc(c.owner_detail ? `${c.owner_detail.first_name} ${c.owner_detail.last_name}` : "—")}</td>
      <td class="mono">${ago(c.last_contacted_at)}</td>
    </tr>`).join("");
  root.innerHTML = shell("contacts", "OBJECTS / <b>CONTACTS</b>", `
    <div class="page-head"><h1>Contacts</h1><span class="meta">${data.count} records</span>
      <div class="actions"><button class="btn btn-primary btn-sm" id="new-contact">New contact</button></div></div>
    <div class="filter-bar">
      <input class="input" style="width:220px" id="csearch" placeholder="Filter contacts…  ( / )" value="${esc(q)}">
      ${["", "lead", "prospect", "customer"].map((s) =>
        `<span class="chip" data-stage="${s}" style="${stage === s ? "border-color:var(--amaranth)" : ""}">${s || "All stages"}</span>`).join("")}
      <span class="spacer"></span>
      <div class="density-toggle"><button class="on" data-density="comfortable">Comfortable</button><button data-density="compact">Compact</button></div>
    </div>
    <div class="table-wrap"><table class="editorial">
      <thead><tr><th>Name</th><th>Company</th><th>Role</th><th>Stage</th><th>Owner</th><th>Last contact</th></tr></thead>
      <tbody>${rows || `<tr><td colspan="6"><div class="empty"><h3>No contacts match.</h3><p>Clear the filters or create the first contact.</p></div></td></tr>`}</tbody>
    </table></div>`);
  wireShell();
  document.querySelectorAll("[data-go]").forEach((tr) => tr.addEventListener("click", () => (location.hash = tr.dataset.go)));
  document.querySelectorAll(".chip[data-stage]").forEach((ch) =>
    ch.addEventListener("click", () => (location.hash = `#/contacts?stage=${ch.dataset.stage}${q ? `&search=${q}` : ""}`)));
  const search = document.getElementById("csearch");
  let t;
  search.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => (location.hash = `#/contacts?search=${encodeURIComponent(search.value)}${stage ? `&stage=${stage}` : ""}`), 350); });
  document.querySelectorAll(".density-toggle button").forEach((b) => b.addEventListener("click", () => {
    b.parentElement.querySelectorAll("button").forEach((x) => x.classList.remove("on"));
    b.classList.add("on");
    document.querySelector("table.editorial").classList.toggle("compact", b.dataset.density === "compact");
  }));
  document.getElementById("new-contact").addEventListener("click", () =>
    modal(`<h2 class="serif">New contact</h2><form id="cform">
      <div class="grid-2"><div class="field"><label>First name</label><input class="input" name="first_name" required></div>
      <div class="field"><label>Last name</label><input class="input" name="last_name"></div></div>
      <div class="field"><label>Email</label><input class="input" name="email" type="email"></div>
      <div class="grid-2"><div class="field"><label>Role</label><input class="input" name="role"></div>
      <div class="field"><label>Stage</label><select class="select" name="stage"><option>lead</option><option>prospect</option><option>customer</option></select></div></div>
      <div class="foot"><button type="button" class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
      <button class="btn btn-primary">Create</button></div></form>`,
    (o) => o.querySelector("#cform").addEventListener("submit", async (e) => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(e.target));
      const c = await API.post("/contacts/", f);
      o.remove(); toast("Contact created"); location.hash = `#/contacts/${c.id}`;
    })));
}

async function contactDetail(id) {
  const [c, timeline] = await Promise.all([API.get(`/contacts/${id}/`), API.get(`/contacts/${id}/timeline/`)]);
  const [dealsData, tasksData] = await Promise.all([
    API.get(`/deals/?search=${encodeURIComponent(c.name)}`),
    API.get(`/tasks/?open=1`),
  ]);
  const deals = (dealsData.results || []).filter((d) => d.contact === c.id);
  const tasks = (tasksData.results || []).filter((t) => t.contact === c.id);
  const KIND_LABEL = { email: "Email", call: "Call logged", whatsapp: "WhatsApp", note: "Note", system: "" };
  const byDay = {};
  timeline.forEach((a) => {
    const day = new Date(a.created_at).toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" });
    (byDay[day] = byDay[day] || []).push(a);
  });
  const tl = Object.entries(byDay).map(([day, acts]) => `
    <div class="tl-day">${day}</div>
    ${acts.map((a) => `<div class="tl-item">
      <span class="when">${new Date(a.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false })}</span>
      <span><b>${KIND_LABEL[a.kind] || a.kind}</b>${a.subject ? ` — ${esc(a.subject)}` : ""}${a.body ? ` <span class="muted">${esc(a.body)}</span>` : ""}</span>
    </div>`).join("")}`).join("");

  root.innerHTML = shell("contacts", `OBJECTS / <a href="#/contacts">CONTACTS</a> / <b>${esc(c.name).toUpperCase()}</b>`, `
  <div class="detail">
    <div class="identity card" style="padding:32px">
      <span class="avatar lg ${avc(c.name)}">${initials(c.name)}</span>
      <h1 class="serif">${esc(c.name)}</h1>
      <div class="muted">${esc(c.role || "")}${c.company_name ? ` · ${esc(c.company_name)}` : ""}</div>
      <div class="meta-grid">
        <span>EMAIL<b>${esc(c.email || "—")}</b></span>
        <span>PHONE<b>${esc(c.phone || "—")}</b></span>
        <span>CREATED<b>${new Date(c.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</b></span>
        <span>LAST CONTACT<b>${ago(c.last_contacted_at)}</b></span>
        <span>OWNER<b>${esc(c.owner_detail ? `${c.owner_detail.first_name} ${c.owner_detail.last_name}` : "—")}</b></span>
        <span>STAGE<b style="color:var(--brook-ink)">${esc(c.stage)}</b></span>
        <span style="grid-column:1/-1">TAGS<span style="display:flex;gap:6px;margin-top:6px">
          ${(c.tags_detail || []).map((t) => `<span class="tag ${t.color === "brook" ? "green" : t.color === "olive" ? "olive" : ""}">${esc(t.name)}</span>`).join("") || "—"}</span></span>
      </div>
      <div style="margin-top:20px;display:flex;gap:8px">
        <button class="btn btn-secondary btn-sm" id="add-note">Add note</button>
        <button class="btn btn-ghost btn-sm" id="log-call">Log call</button>
      </div>
    </div>
    <div>
      <div class="tabs">
        <a href="#" class="active" data-tab="timeline">Timeline</a>
        <a href="#" data-tab="deals">Deals · ${deals.length}</a>
        <a href="#" data-tab="tasks">Tasks · ${tasks.length}</a>
      </div>
      <div data-pane="timeline"><div class="timeline">${tl || '<p class="muted">No activity yet.</p>'}</div></div>
      <div data-pane="deals" style="display:none"><table class="editorial">
        <thead><tr><th>Deal</th><th>Stage</th><th>Value</th><th>Close</th></tr></thead>
        <tbody>${deals.map((d) => `<tr><td class="name">${esc(d.name)}</td>
          <td><span class="tag green">${esc(d.stage)}</span></td><td class="mono">${inr(d.value)}</td>
          <td class="mono">${d.close_date || "—"}</td></tr>`).join("") || '<tr><td colspan="4" class="muted">No deals.</td></tr>'}</tbody></table></div>
      <div data-pane="tasks" style="display:none"><table class="editorial">
        <tbody>${tasks.map((t) => `<tr><td style="width:32px"><label class="check"><input type="checkbox" data-complete="${t.id}"></label></td>
          <td class="name">${esc(t.title)}</td><td class="mono">${t.due_at ? ago(t.due_at) : "—"}</td></tr>`).join("") || '<tr><td class="muted">No open tasks.</td></tr>'}</tbody></table></div>
    </div>
  </div>`);
  wireShell();
  document.querySelectorAll(".tabs a").forEach((tab) => tab.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelectorAll(".tabs a").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    document.querySelectorAll("[data-pane]").forEach((p) => (p.style.display = p.dataset.pane === tab.dataset.tab.split(" ")[0] ? "" : "none"));
  }));
  const addActivity = (kind, title) => modal(`<h2 class="serif">${title}</h2><form id="aform">
      <div class="field"><label>Subject</label><input class="input" name="subject"></div>
      <div class="field"><label>Details</label><textarea class="input" name="body" rows="4"></textarea></div>
      <div class="foot"><button type="button" class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
      <button class="btn btn-primary">Save</button></div></form>`,
    (o) => o.querySelector("#aform").addEventListener("submit", async (e) => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(e.target));
      await API.post("/activities/", { ...f, contact: c.id, kind });
      o.remove(); toast("Saved"); render();
    }));
  document.getElementById("add-note").addEventListener("click", () => addActivity("note", "Add note"));
  document.getElementById("log-call").addEventListener("click", () => addActivity("call", "Log call"));
  document.querySelectorAll("[data-complete]").forEach((cb) => cb.addEventListener("change", async () => {
    await API.post(`/tasks/${cb.dataset.complete}/complete/`, {});
    toast("Task completed"); render();
  }));
}

async function dealsView() {
  const board = await API.get("/deals/board/");
  const cols = board.map((col) => `
    <div class="kcol" data-stage="${col.stage}">
      <div class="kcol-head"><b>${col.label}</b><span class="meta">${col.count} · ${inr(col.total)} wtd ${inr(col.weighted)}</span></div>
      ${col.deals.map((d) => `
        <div class="kcard" draggable="true" data-deal="${d.id}" ${col.stage === "lost" ? 'style="opacity:.65"' : ""}>
          <div class="co">${esc(d.company_name || d.contact_name || "—")}</div>
          <div class="title">${esc(d.name)}</div>
          <div class="foot"><span class="value">${inr(d.value)}</span>
            <span class="avatar-row"><span class="avatar ${avc(d.owner_detail?.username)}">${initials(d.owner_detail ? `${d.owner_detail.first_name} ${d.owner_detail.last_name}` : "?")}</span></span></div>
        </div>`).join("")}
    </div>`).join("");
  const open = board.filter((c) => !["won", "lost"].includes(c.stage));
  const total = open.reduce((s, c) => s + Number(c.total), 0);
  const weighted = open.reduce((s, c) => s + Number(c.weighted), 0);
  root.innerHTML = shell("deals", "OBJECTS / <b>DEALS</b> / PIPELINE: DEFAULT", `
    <div class="page-head"><h1>Deals</h1><span class="meta">pipeline ${inr(total)} · weighted ${inr(weighted)}</span></div>
    <div class="kanban">${cols}</div>
    <p class="meta" style="margin-top:8px">Drag cards between stages — the change persists via PATCH /api/deals/:id/</p>`);
  wireShell();
  let dragged = null;
  document.querySelectorAll(".kcard[draggable]").forEach((card) => {
    card.addEventListener("dragstart", () => (dragged = card.dataset.deal));
  });
  document.querySelectorAll(".kcol").forEach((col) => {
    col.addEventListener("dragover", (e) => { e.preventDefault(); col.classList.add("dropover"); });
    col.addEventListener("dragleave", () => col.classList.remove("dropover"));
    col.addEventListener("drop", async (e) => {
      e.preventDefault(); col.classList.remove("dropover");
      if (!dragged) return;
      await API.patch(`/deals/${dragged}/`, { stage: col.dataset.stage });
      toast(`Moved to ${col.dataset.stage}`); render();
    });
  });
}

async function tasksView() {
  const data = await API.get("/tasks/?open=1");
  const now = Date.now();
  const groups = { Overdue: [], Today: [], Upcoming: [], "No due date": [] };
  (data.results || []).forEach((t) => {
    if (!t.due_at) groups["No due date"].push(t);
    else if (new Date(t.due_at) < now && new Date(t.due_at).toDateString() !== new Date().toDateString()) groups.Overdue.push(t);
    else if (new Date(t.due_at).toDateString() === new Date().toDateString()) groups.Today.push(t);
    else groups.Upcoming.push(t);
  });
  const gh = Object.entries(groups).filter(([, ts]) => ts.length).map(([g, ts]) => `
    <div class="tgroup" style="margin-bottom:32px">
      <h2 class="serif" style="font-size:18px;font-weight:400;margin-bottom:4px">${g}<span class="meta" style="font-family:var(--mono);font-size:11px;margin-left:8px">${ts.length} TASKS</span></h2>
      <table class="editorial"><tbody>
      ${ts.map((t) => `<tr>
        <td style="width:32px"><label class="check"><input type="checkbox" data-complete="${t.id}"></label></td>
        <td class="name">${esc(t.title)}${t.recurrence ? ` <span class="tag olive">↻ ${t.recurrence}</span>` : ""}${t.blocked_by_title ? ` <span class="tag">blocked: ${esc(t.blocked_by_title)}</span>` : ""}</td>
        <td>${t.contact_name ? `<a href="#/contacts/${t.contact}">${esc(t.contact_name)}</a>` : "—"}</td>
        <td class="muted">${esc(t.deal_name || "")}</td>
        <td class="mono ${g === "Overdue" ? "" : ""}" ${g === "Overdue" ? 'style="color:var(--amaranth);font-weight:500"' : ""}>${t.due_at ? new Date(t.due_at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "—"}</td>
      </tr>`).join("")}
      </tbody></table>
    </div>`).join("");
  root.innerHTML = shell("tasks", "OBJECTS / <b>TASKS</b>", `
    <div class="page-head"><h1>Tasks</h1><span class="meta">${data.count} open</span>
      <div class="actions"><button class="btn btn-primary btn-sm" id="new-task">New task</button></div></div>
    ${gh || '<div class="empty"><h3>All clear.</h3><p>Nothing due. Go close a deal.</p></div>'}`);
  wireShell();
  document.querySelectorAll("[data-complete]").forEach((cb) => cb.addEventListener("change", async () => {
    await API.post(`/tasks/${cb.dataset.complete}/complete/`, {});
    toast("Task completed"); render();
  }));
  document.getElementById("new-task").addEventListener("click", () =>
    modal(`<h2 class="serif">New task</h2><form id="tform">
      <div class="field"><label>Title</label><input class="input" name="title" required></div>
      <div class="grid-2"><div class="field"><label>Due</label><input class="input" type="datetime-local" name="due_at"></div>
      <div class="field"><label>Recurrence</label><select class="select" name="recurrence"><option value="">None</option><option>daily</option><option>weekly</option><option>monthly</option></select></div></div>
      <div class="foot"><button type="button" class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
      <button class="btn btn-primary">Create</button></div></form>`,
    (o) => o.querySelector("#tform").addEventListener("submit", async (e) => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(e.target));
      if (!f.due_at) delete f.due_at;
      await API.post("/tasks/", { ...f, assignee: API.user?.id });
      o.remove(); toast("Task created"); render();
    })));
}

async function reportsView() {
  const r = await API.get("/reports/summary/");
  const stageLabel = { qualified: "Qualified", proposal: "Proposal", negotiation: "Negotiation" };
  const stageColor = { qualified: "#9F9679", proposal: "#933B5B", negotiation: "#B5728A" };
  const maxStage = Math.max(...r.by_stage.map((s) => Number(s.total)), 1);
  const bars = r.by_stage.map((s, i) => {
    const w = Math.max(24, (Number(s.total) / maxStage) * 560);
    const y = 20 + i * 50;
    return `<text x="130" y="${y + 15}" text-anchor="end">${stageLabel[s.stage] || s.stage}</text>
      <rect x="140" y="${y}" width="${w}" height="22" rx="4" fill="${stageColor[s.stage] || "#9F9679"}"><title>${stageLabel[s.stage]} — ${inr(s.total)} (${s.count} deals)</title></rect>
      <text x="${145 + w}" y="${y + 15}" fill="#5c5744">${inr(s.total)}</text>`;
  }).join("");
  const months = r.won_by_month.slice(-6);
  const maxWon = Math.max(...months.map((m) => Number(m.total)), 1);
  const pts = months.map((m, i) => {
    const x = 80 + i * (600 / Math.max(months.length - 1, 1));
    const y = 180 - (Number(m.total) / maxWon) * 140;
    return { x, y, m };
  });
  const line = pts.map((p) => `${p.x},${p.y}`).join(" ");
  const dots = pts.map((p) => `<circle cx="${p.x}" cy="${p.y}" r="4" fill="#933B5B" stroke="#E3D6BF" stroke-width="2"><title>${new Date(p.m.month).toLocaleDateString("en-IN", { month: "short" })} — ${inr(p.m.total)}</title></circle>
    <text x="${p.x}" y="202" text-anchor="middle">${new Date(p.m.month).toLocaleDateString("en-IN", { month: "short" }).toUpperCase()}</text>`).join("");
  const last = pts[pts.length - 1];
  root.innerHTML = shell("reports", "INSIGHTS / <b>REPORTS</b> / PIPELINE HEALTH", `
    <article style="max-width:760px;margin:0 auto">
      <div class="page-head" style="margin-bottom:4px"><h1 style="font-size:32px">Pipeline health</h1>
        <div class="actions"><button class="btn btn-primary btn-sm" onclick="window.print()">Export PDF</button></div></div>
      <div class="meta" style="margin-bottom:24px">GENERATED ${new Date(r.generated_at).toLocaleString("en-IN").toUpperCase()} · LIVE DATA · ALL OWNERS</div>
      <div class="stat-row">
        <div class="stat"><div class="n">${inr(r.open_total)}</div><div class="l">Open pipeline value</div></div>
        <div class="stat"><div class="n">${inr(r.open_weighted)}</div><div class="l">Probability-weighted</div></div>
        <div class="stat"><div class="n">${r.contact_count}</div><div class="l">Contacts · ${r.open_task_count} open tasks</div></div>
      </div>
      <figure class="fig"><div class="fig-title">Open pipeline value by stage</div>
        <svg viewBox="0 0 760 ${30 + r.by_stage.length * 50}"><line x1="140" y1="10" x2="140" y2="${20 + r.by_stage.length * 50}" stroke="rgba(159,150,121,.3)"/>${bars}</svg>
        <figcaption>FIG 1 · SOURCE: LIVE DEALS · EXCLUDES WON/LOST</figcaption></figure>
      <figure class="fig"><div class="fig-title">Won revenue by month</div>
        <svg viewBox="0 0 760 220">
          <line x1="60" y1="180" x2="720" y2="180" stroke="rgba(159,150,121,.25)"/>
          <polyline fill="none" stroke="#933B5B" stroke-width="2" stroke-linejoin="round" points="${line}"/>
          ${dots}
          ${last ? `<text x="${last.x}" y="${last.y - 12}" text-anchor="middle" fill="#5c5744">${inr(last.m.total)}</text>` : ""}
        </svg>
        <figcaption>FIG 2 · DEALS MARKED WON · GROUPED BY STAGE-CHANGE MONTH</figcaption></figure>
      <p style="font-size:15px;line-height:1.7" class="muted">This report renders from live workspace data.
      Values are direct-labeled by design — the Darvin palette is intentionally muted, so identity never rides on color alone.</p>
    </article>`);
  wireShell();
}

async function automationsView() {
  const data = await API.get("/automations/");
  const autos = data.results || data;
  root.innerHTML = shell("automations", "INSIGHTS / <b>AUTOMATIONS</b>", `
    <div class="page-head"><h1>Automations</h1>
      <span class="meta">${autos.filter((a) => a.active).length} active · ${autos.reduce((s, a) => s + a.run_count, 0)} total runs</span></div>
    ${autos.map((a) => `
      <div class="card" style="margin-bottom:12px;display:flex;align-items:center;gap:20px">
        <div style="flex:1">
          <b style="font-size:15px;color:var(--amaranth-deep)">${esc(a.name)}</b>
          <div class="meta" style="margin-top:4px">WHEN ${esc(a.trigger).toUpperCase()}${a.condition ? ` · IF ${esc(a.condition)}` : ""}</div>
          <div class="meta">THEN ${esc(a.action)}</div>
          <div class="meta" style="margin-top:4px">RAN ${a.run_count}× · LAST ${ago(a.last_run_at)}</div>
        </div>
        <button class="btn btn-secondary btn-sm" data-run="${a.id}">Run now</button>
        <input type="checkbox" class="toggle" data-toggle="${a.id}" ${a.active ? "checked" : ""}>
      </div>`).join("")}`);
  wireShell();
  document.querySelectorAll("[data-run]").forEach((b) => b.addEventListener("click", async () => {
    const res = await API.post(`/automations/${b.dataset.run}/run/`, {});
    toast(`Ran — ${res.tasks_created} task(s) created`); render();
  }));
  document.querySelectorAll("[data-toggle]").forEach((t) => t.addEventListener("change", async () => {
    await API.patch(`/automations/${t.dataset.toggle}/`, { active: t.checked });
    toast(t.checked ? "Activated" : "Paused");
  }));
}

// ── Router ───────────────────────────────────────────────────
async function render() {
  const hash = location.hash || "#/contacts";
  const [path, query] = hash.slice(2).split("?");
  const params = new URLSearchParams(query || "");
  if (!API.token) return loginView();
  try {
    const seg = path.split("/");
    if (seg[0] === "login") return loginView();
    if (seg[0] === "contacts" && seg[1]) return await contactDetail(seg[1]);
    if (seg[0] === "deals") return await dealsView();
    if (seg[0] === "tasks") return await tasksView();
    if (seg[0] === "reports") return await reportsView();
    if (seg[0] === "automations") return await automationsView();
    return await contactsView(params);
  } catch (err) {
    if (err.message !== "Signed out") {
      root.innerHTML = `<div class="empty" style="padding-top:120px"><h3>Something broke.</h3><p class="mono">${esc(err.message)}</p></div>`;
    }
  }
}

window.addEventListener("hashchange", render);
render();
