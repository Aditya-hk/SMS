// ui.js - navigation, page guard and small helpers. Loaded SECOND on every page.

const HOME_BY_ROLE = {
  CITIZEN: "/pages/citizen/dashboard.html",
  OFFICER: "/pages/officer/dashboard.html",
  CONTRACTOR: "/pages/contractor/dashboard.html",
  ADMIN: "/pages/admin/dashboard.html",
};

// ---- safety: escape text before putting it into HTML (prevents XSS) ----
function esc(value) {
  if (value === null || value === undefined) return "";
  return String(value).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );
}

// ---- formatting ----
const fmtDate = (d) => (d ? String(d).slice(0, 10) : "-");
const fmtMoney = (n) => "Rs. " + Number(n || 0).toLocaleString("en-IN");
const badge = (s) => (s ? `<span class="badge ${esc(s)}">${esc(String(s).replace(/_/g, " "))}</span>` : "-");
const progressBar = (p) =>
  `<div class="bar-outer"><div class="bar-inner" style="width:${Number(p) || 0}%"></div></div><small>${Number(p) || 0}%</small>`;
const $ = (id) => document.getElementById(id);
const queryParam = (name) => new URLSearchParams(window.location.search).get(name);

// ---- messages ----
function showMessage(type, text, elementId = "page-message") {
  const el = $(elementId);
  if (!el) return;
  el.innerHTML = text ? `<div class="message ${type}">${esc(text)}</div>` : "";
  if (text) el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ---- frontend validation (the backend validates again - never trust the browser) ----
const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
const isPhone = (v) => /^\+?[0-9]{10,13}$/.test(v);
const isStrongPassword = (v) => v.length >= 8 && /[a-z]/.test(v) && /[A-Z]/.test(v) && /[0-9]/.test(v);

// ---- tables ----
// columns: [{ label: "Title", render: (row) => "html" }]
function buildTable(columns, rows, emptyText = "No records found.") {
  if (!rows || rows.length === 0) return `<div class="card">${esc(emptyText)}</div>`;
  const head = columns.map((c) => `<th>${esc(c.label)}</th>`).join("");
  const body = rows
    .map((r) => "<tr>" + columns.map((c) => `<td>${c.render(r)}</td>`).join("") + "</tr>")
    .join("");
  return `<div class="table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

// ---- fill a <select> from an API list ----
async function fillSelect(selectId, path, labelFn, { blank = "-- select --", valueKey = "id" } = {}) {
  const res = await api(path);
  $(selectId).innerHTML =
    `<option value="">${esc(blank)}</option>` +
    res.data.map((r) => `<option value="${esc(r[valueKey])}">${esc(labelFn(r))}</option>`).join("");
  return res.data;
}

// ---- alerts list (used on several pages) ----
function renderAlerts(alerts) {
  if (!alerts.length) return "<p>No active alerts.</p>";
  return alerts
    .map(
      (a) =>
        `<div class="alert-item ${esc(a.severity)}"><strong>${esc(a.title)}</strong>
        ${badge(a.severity)}<br>${esc(a.message)}<br><small>${fmtDate(a.created_at)}${
          a.expires_at ? " | valid until " + fmtDate(a.expires_at) : ""
        }</small></div>`,
    )
    .join("");
}

// ---- tabs: initTabs({ complaints: loadComplaints, projects: loadProjects }) ----
function initTabs(loaders) {
  const buttons = document.querySelectorAll(".tabs button");
  async function show(name) {
    buttons.forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
    document
      .querySelectorAll(".panel")
      .forEach((p) => p.classList.toggle("active", p.id === "panel-" + name));
    showMessage("info", "");
    try {
      await loaders[name]();
    } catch (e) {
      showMessage("error", e.message);
    }
  }
  buttons.forEach((b) => b.addEventListener("click", () => show(b.dataset.tab)));
  show(buttons[0].dataset.tab);
}

// ---- header / navigation ----
async function logout() {
  try {
    await api("/auth/logout", { method: "POST", noRedirect: true });
  } catch (e) {
    /* ignore */
  }
  Session.clear();
  window.location.href = "/pages/login.html";
}

function renderHeader() {
  const user = Session.getUser();
  const links = [
    ["/index.html", "Home"],
    ["/pages/transparency.html", "Transparency"],
    ["/pages/roads.html", "Roads"],
    ["/pages/projects.html", "Projects"],
    ["/pages/contractors.html", "Contractors"],
    ["/pages/complaint-status.html", "Complaint Status"],
  ];
  const roleLinks = {
    CITIZEN: [
      ["/pages/citizen/dashboard.html", "Dashboard"],
      ["/pages/citizen/submit-complaint.html", "Submit Complaint"],
      ["/pages/citizen/my-complaints.html", "My Complaints"],
      ["/pages/citizen/profile.html", "Profile"],
    ],
    OFFICER: [["/pages/officer/dashboard.html", "Officer Dashboard"]],
    CONTRACTOR: [["/pages/contractor/dashboard.html", "Contractor Dashboard"]],
    ADMIN: [["/pages/admin/dashboard.html", "Admin Dashboard"]],
  };
  let nav = (user ? roleLinks[user.role] : []).concat(links);
  const path = window.location.pathname;
  let html = nav
    .map(([href, label]) => `<a href="${href}" class="${path === href ? "active" : ""}">${label}</a>`)
    .join("");
  if (user)
    html += `<span class="who">${esc(user.full_name)} (${esc(user.role)})</span><button id="logout-btn">Logout</button>`;
  else html += `<a href="/pages/login.html">Login</a><a href="/pages/register.html">Register</a>`;
  const el = $("site-header");
  if (el) {
    el.className = "site-header";
    el.innerHTML = `<div class="bar"><a class="brand" href="/index.html">Smart Municipal Corporation</a><nav>${html}</nav></div>`;
    const btn = $("logout-btn");
    if (btn) btn.addEventListener("click", logout);
  }
}

// ---- page guard: <body data-role="CITIZEN"> means only citizens may open this page ----
function guard(allowedRoles) {
  const user = Session.getUser();
  if (!user || !Session.getToken()) {
    window.location.href = "/pages/login.html";
    return false;
  }
  if (!allowedRoles.includes(user.role)) {
    window.location.href = HOME_BY_ROLE[user.role];
    return false;
  }
  return true; // NOTE: this only improves navigation. The BACKEND is what really protects the data.
}

// ---- every page script calls initPage({ "page-name": function }) ----
function initPage(handlers) {
  document.addEventListener("DOMContentLoaded", async () => {
    renderHeader();
    const roles = document.body.dataset.role;
    if (roles && !guard(roles.split(","))) return;
    const handler = handlers[document.body.dataset.page];
    if (handler) {
      try {
        await handler();
      } catch (e) {
        showMessage("error", e.message);
      }
    }
  });
}
