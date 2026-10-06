// admin.js - admin dashboard (body has data-role="ADMIN").
// A small "CRUD engine": each resource below is described by a config object
// (API URL, table columns, form fields) and ONE set of functions builds the
// list, the add/edit form and the delete button for all of them.

const YESNO = [
  ["1", "Active"],
  ["0", "Disabled"],
];
const CONDITIONS = ["GOOD", "FAIR", "POOR", "UNDER_REPAIR"];

const col = (label, key, fmt) => ({ label, render: (r) => (fmt ? fmt(r[key]) : esc(r[key])) });

const RESOURCES = {
  officers: {
    title: "Officer",
    list: "/officers",
    url: "/officers",
    columns: [
      col("Name", "full_name"),
      col("Email", "email"),
      col("Phone", "phone"),
      col("Department", "department"),
      col("Designation", "designation"),
      { label: "Active", render: (r) => (r.is_active ? "Yes" : "No") },
    ],
    fields: [
      { key: "full_name", label: "Full name", required: true },
      { key: "email", label: "Email", required: true, createOnly: true },
      { key: "password", label: "Password", type: "password", required: true, createOnly: true },
      { key: "phone", label: "Phone" },
      { key: "department", label: "Department", required: true },
      { key: "designation", label: "Designation", required: true },
      { key: "is_active", label: "Account", type: "select", options: YESNO, editOnly: true, numeric: true },
    ],
  },
  contractors: {
    title: "Contractor",
    list: "/contractors/details",
    url: "/contractors",
    columns: [
      col("Company", "company_name"),
      col("License", "license_no"),
      col("Contact", "full_name"),
      col("Email", "email"),
      col("Phone", "phone"),
      { label: "Active", render: (r) => (r.is_active ? "Yes" : "No") },
    ],
    fields: [
      { key: "full_name", label: "Contact person", required: true },
      { key: "email", label: "Email", required: true, createOnly: true },
      { key: "password", label: "Password", type: "password", required: true, createOnly: true },
      { key: "phone", label: "Phone" },
      { key: "company_name", label: "Company name", required: true },
      { key: "license_no", label: "License number", required: true },
      { key: "address", label: "Address" },
      { key: "is_active", label: "Account", type: "select", options: YESNO, editOnly: true, numeric: true },
    ],
  },
  locations: {
    title: "Location",
    list: "/locations",
    url: "/locations",
    columns: [col("Area", "area_name"), col("Ward", "ward"), col("Pincode", "pincode")],
    fields: [
      { key: "area_name", label: "Area name", required: true },
      { key: "ward", label: "Ward", required: true },
      { key: "pincode", label: "Pincode (6 digits)", required: true },
    ],
  },
  roads: {
    title: "Road",
    list: "/roads",
    url: "/roads",
    columns: [
      col("Name", "name"),
      col("Area", "area_name"),
      col("Length km", "length_km"),
      col("Condition", "road_condition", badge),
      col("Last maintained", "last_maintained_date", fmtDate),
    ],
    fields: [
      { key: "name", label: "Road name", required: true },
      {
        key: "location_id",
        label: "Location",
        type: "ref",
        required: true,
        from: { url: "/locations", label: (l) => `${l.area_name} (${l.ward})` },
      },
      { key: "length_km", label: "Length (km)", type: "number", required: true },
      { key: "width_m", label: "Width (m)", type: "number" },
      { key: "road_condition", label: "Condition", type: "select", options: CONDITIONS, required: true },
      { key: "last_maintained_date", label: "Last maintained", type: "date" },
    ],
  },
  pipelines: {
    title: "Pipeline",
    list: "/pipelines",
    url: "/pipelines",
    columns: [
      col("Name", "name"),
      col("Type", "pipeline_type"),
      col("Area", "area_name"),
      col("Length km", "length_km"),
      col("Status", "status", badge),
      col("Installed", "installed_year"),
    ],
    fields: [
      { key: "name", label: "Pipeline name", required: true },
      {
        key: "location_id",
        label: "Location",
        type: "ref",
        required: true,
        from: { url: "/locations", label: (l) => `${l.area_name} (${l.ward})` },
      },
      {
        key: "pipeline_type",
        label: "Type",
        type: "select",
        options: ["WATER", "SEWER", "GAS", "STORM_DRAIN"],
        required: true,
      },
      { key: "length_km", label: "Length (km)", type: "number", required: true },
      {
        key: "status",
        label: "Status",
        type: "select",
        options: ["ACTIVE", "UNDER_MAINTENANCE", "DAMAGED"],
        required: true,
      },
      { key: "installed_year", label: "Installed year", type: "number" },
    ],
  },
  projects: {
    title: "Project",
    list: "/projects",
    url: "/projects",
    columns: [
      col("Title", "title"),
      col("Status", "status", badge),
      col("Budget", "budget", fmtMoney),
      col("Officer", "officer_name"),
      col("Contractor", "company_name"),
      col("Progress", "progress_percent", progressBar),
      col("Expected end", "expected_completion_date", fmtDate),
    ],
    fields: [
      { key: "title", label: "Title", required: true },
      {
        key: "location_id",
        label: "Location",
        type: "ref",
        required: true,
        from: { url: "/locations", label: (l) => `${l.area_name} (${l.ward})` },
      },
      { key: "road_id", label: "Road", type: "ref", from: { url: "/roads", label: (r) => r.name } },
      {
        key: "pipeline_id",
        label: "Pipeline",
        type: "ref",
        from: { url: "/pipelines", label: (p) => p.name },
      },
      {
        key: "officer_id",
        label: "Officer",
        type: "ref",
        from: { url: "/officers", label: (o) => o.full_name },
      },
      {
        key: "contractor_id",
        label: "Contractor",
        type: "ref",
        from: { url: "/contractors/details", label: (c) => c.company_name },
      },
      { key: "budget", label: "Budget (Rs.)", type: "number", required: true },
      { key: "start_date", label: "Start date", type: "date" },
      { key: "expected_completion_date", label: "Expected completion", type: "date" },
      { key: "actual_completion_date", label: "Actual completion", type: "date" },
      {
        key: "status",
        label: "Status",
        type: "select",
        options: ["PLANNED", "APPROVED", "IN_PROGRESS", "COMPLETED", "CANCELLED"],
        required: true,
      },
      { key: "description", label: "Description", type: "textarea" },
      { key: "remarks", label: "Remarks" },
    ],
  },
  payments: {
    title: "Payment",
    list: "/payments",
    url: "/payments",
    columns: [
      col("Date", "payment_date", fmtDate),
      col("Project", "project_title"),
      col("Contractor", "company_name"),
      col("Amount", "amount", fmtMoney),
      col("Status", "status", badge),
      col("Description", "description"),
    ],

    fields: [
      {
        key: "project_id",
        label: "Project",
        type: "ref",
        required: true,
        from: { url: "/projects", label: (p) => p.title },
      },
      { key: "amount", label: "Amount (Rs.)", type: "number", required: true },
      { key: "payment_date", label: "Payment date", type: "date", required: true },
      {
        key: "status",
        label: "Status",
        type: "select",
        options: ["PENDING", "PAID", "REJECTED"],
        required: true,
      },
      { key: "description", label: "Description" },
    ],
  },
  maintenance: {
    title: "Maintenance",
    list: "/maintenance",
    url: "/maintenance",
    columns: [
      col("Work", "description"),
      { label: "Asset", render: (r) => esc(r.road_name || r.pipeline_name || "-") },
      col("Date", "maintenance_date", fmtDate),
      col("Status", "status", badge),
      col("Contractor", "company_name"),
      col("Officer", "officer_name"),
    ],
    fields: [
      { key: "description", label: "Description", required: true },
      { key: "maintenance_date", label: "Date", type: "date", required: true },
      {
        key: "status",
        label: "Status",
        type: "select",
        options: ["SCHEDULED", "IN_PROGRESS", "COMPLETED"],
        required: true,
      },
      { key: "road_id", label: "Road", type: "ref", from: { url: "/roads", label: (r) => r.name } },
      {
        key: "pipeline_id",
        label: "Pipeline",
        type: "ref",
        from: { url: "/pipelines", label: (p) => p.name },
      },
      { key: "project_id", label: "Project", type: "ref", from: { url: "/projects", label: (p) => p.title } },
      {
        key: "assigned_contractor_id",
        label: "Contractor",
        type: "ref",
        from: { url: "/contractors/details", label: (c) => c.company_name },
      },
      {
        key: "assigned_officer_id",
        label: "Officer",
        type: "ref",
        from: { url: "/officers", label: (o) => o.full_name },
      },
    ],
  },
  alerts: {
    title: "Alert",
    list: "/alerts",
    url: "/alerts",
    columns: [
      col("Title", "title"),
      col("Severity", "severity", badge),
      col("Audience", "audience"),
      col("Expires", "expires_at", fmtDate),
      col("Message", "message"),
    ],
    fields: [
      { key: "title", label: "Title", required: true },
      { key: "message", label: "Message", type: "textarea", required: true },
      {
        key: "severity",
        label: "Severity",
        type: "select",
        options: ["INFO", "WARNING", "CRITICAL"],
        required: true,
      },
      { key: "audience", label: "Audience", type: "select", options: ["PUBLIC", "OFFICER"], required: true },
      { key: "expires_at", label: "Expiry date", type: "date" },
    ],
  },
};

const rowsCache = {};

// ---------- list + toolbar ----------
async function renderCrud(name) {
  const cfg = RESOURCES[name];

  const rows = (await api(cfg.list)).data;
  rowsCache[name] = rows;
  const columns = cfg.columns.concat([
    {
      label: "",
      render: (r) =>
        `<div class="actions"><button class="btn small" data-edit="${name}:${r.id}">Edit</button><button class="btn small danger"
           data-del="${name}:${r.id}">Delete</button></div>`,
    },
  ]);
  $("crud-" + name).innerHTML =
    `<div class="toolbar"><button class="btn" data-add="${name}">+ Add ${esc(cfg.title)}</button></div><div id="form-${name}"></div>` +
    buildTable(columns, rows);
}

// ---------- form ----------
async function fieldHtml(f, value, name) {
  const attrs = `name="${f.key}" id="f-${name}-${f.key}"`;
  if (f.type === "textarea") return `<textarea ${attrs}>${esc(value)}</textarea>`;
  if (f.type === "select" || f.type === "ref") {
    let options;
    if (f.type === "select")
      options = f.options.map((o) => (Array.isArray(o) ? o : [o, o.replace(/_/g, " ")]));
    else {
      const data = (await api(f.from.url)).data;
      options = [["", f.required ? "-- select --" : "-- none --"]].concat(
        data.map((r) => [r.id, f.from.label(r)]),
      );
    }
    return (
      `<select ${attrs}>` +
      options
        .map(
          ([v, l]) =>
            `<option value="${esc(v)}" ${String(v) === String(value) ? "selected" : ""}>${esc(l)}</option>`,
        )
        .join("") +
      "</select>"
    );
  }
  const type = f.type === "number" ? 'number" step="any' : f.type || "text";
  return `<input type="${type}" ${attrs} value="${esc(value)}">`;
}

async function showForm(name, row) {
  const cfg = RESOURCES[name];
  const editing = !!row;
  let html = `<div class="card"><h2>${editing ? "Edit" : "Add"} ${esc(cfg.title)}</h2><form data-form="${name}" data-id="${
    editing ? row.id : ""
  }"><div class="form-row">`;
  for (const f of cfg.fields) {
    if ((editing && f.createOnly) || (!editing && f.editOnly)) continue;
    const value = editing && row[f.key] !== null && row[f.key] !== undefined ? row[f.key] : "";
    html += `<div><label for="f-${name}-${f.key}">${esc(f.label)}${f.required ? " *" : ""}</label>${await fieldHtml(
      f,
      value,
      name,
    )}</div>`;
  }
  html += `</div><br><button class="btn" type="submit">Save</button> <button class="btn secondary" type="button"
        data-cancel="${name}">Cancel</button></form></div>`;
  $("form-" + name).innerHTML = html;
}

async function saveForm(form) {
  const name = form.dataset.form;
  const cfg = RESOURCES[name];
  const id = form.dataset.id;
  const body = {};
  for (const f of cfg.fields) {
    if ((id && f.createOnly) || (!id && f.editOnly)) continue;
    const raw = form.elements[f.key].value.trim();
    if (f.required && raw === "") throw new Error(f.label + " is required");
    if (raw === "") body[f.key] = null;
    else if (f.type === "number" || f.type === "ref" || f.numeric) body[f.key] = Number(raw);
    else body[f.key] = raw;
  }
  await api(id ? `${cfg.url}/${id}` : cfg.url, { method: id ? "PUT" : "POST", body });
  showMessage("success", cfg.title + (id ? " updated." : " created."));
  await renderCrud(name);
}

// ---------- complaints tab (special: assign / reject / close) ----------
let activeOfficers = [];
async function loadComplaints() {
  activeOfficers = (await api("/officers")).data.filter((o) => o.is_active);
  const rows = (await api("/complaints")).data;
  const officerSelect = (id) =>
    `<select id="officer-${id}">${activeOfficers
      .map(
        (o) => `<option
         value="${o.id}">${esc(o.full_name)}</option>`,
      )
      .join("")}</select>`;
  $("complaint-list").innerHTML = buildTable(
    [
      { label: "ID", render: (c) => esc(c.id) },
      {
        label: "Complaint",
        render: (c) =>
          `<strong>${esc(c.title)}</strong><br><small>${esc(c.citizen_name)} | ${esc(c.area_name)} |
         ${fmtDate(c.complaint_date)}</small>`,
      },

      { label: "Status", render: (c) => badge(c.status) },
      { label: "Officer", render: (c) => esc(c.officer_name || "-") },
      {
        label: "Actions",
        render: (c) => {
          let a = "";
          if (["SUBMITTED", "ASSIGNED"].includes(c.status))
            a += `<div class="actions">${officerSelect(c.id)}<button class="btn small" data-assign="${c.id}">${
              c.status === "SUBMITTED" ? "Assign" : "Reassign"
            }</button></div>`;
          if (["SUBMITTED", "ASSIGNED"].includes(c.status))
            a += `<button class="btn small danger" data-reject="${c.id}">Reject</button>`;
          if (c.status === "RESOLVED") a += `<button class="btn small" data-close="${c.id}">Close</button>`;
          return a || "-";
        },
      },
    ],
    rows,
  );
}

// ---------- overview and reports ----------
async function loadOverview() {
  const s = (await api("/public/stats")).data;
  const cards = [
    [s.projects.total, "Projects"],
    [s.projects.ongoing, "Ongoing projects"],
    [s.complaints.total, "Complaints"],
    [s.complaints.resolved, "Resolved complaints"],
    [s.contractors, "Contractors"],
    [fmtMoney(s.expenditure_paid), "Paid to contractors"],
  ];
  $("overview-stats").innerHTML = cards
    .map(
      ([n, l]) =>
        `<div class="stat"><div class="num">${esc(n)}</div><div class="label">${esc(l)}</div></div>`,
    )
    .join("");
  const fb = (await api("/feedback")).data;
  $("feedback-list").innerHTML = buildTable(
    [
      col("Complaint", "complaint_title"),
      col("Citizen", "citizen_name"),
      { label: "Rating", render: (f) => "&#9733;".repeat(f.rating) },
      col("Comment", "comment"),
    ],
    fb,
    "No feedback yet.",
  );
}

async function loadReports() {
  const defs = [
    ["Complaints by status", "complaints-by-status", [col("Status", "status", badge), col("Total", "total")]],
    [
      "Projects by status",
      "projects-by-status",
      [col("Status", "status", badge), col("Total", "total"), col("Total budget", "total_budget", fmtMoney)],
    ],
    [
      "Project expenditure",
      "expenditure",
      [
        col("Project", "title"),
        col("Budget", "budget", fmtMoney),
        col("Paid", "paid", fmtMoney),
        col("% paid", "percent_of_budget_paid"),
      ],
    ],
    [
      "Contractor projects",
      "contractor-projects",
      [
        col("Company", "company_name"),
        col("Total", "total_projects"),
        col("Completed", "completed"),
        col("Ongoing", "ongoing"),
        col("Budget", "total_budget", fmtMoney),
      ],
    ],
    [
      "Road maintenance",
      "road-maintenance",
      [
        col("Road", "road"),
        col("Condition", "road_condition", badge),
        col("Jobs", "maintenance_jobs"),
        col("Completed", "completed_jobs"),
        col("Latest", "latest_job", fmtDate),
      ],
    ],
    [
      "Complaint resolution by category",
      "complaint-resolution",
      [
        col("Category", "category"),
        col("Total", "total"),

        col("Resolved", "resolved"),
        col("Average rating", "average_rating"),
      ],
    ],
  ];
  let html = "";
  for (const [title, path, cols] of defs)
    html += `<h2>${esc(title)}</h2>` + buildTable(cols, (await api("/reports/" + path)).data);
  $("report-area").innerHTML = html;
}

// ---------- events ----------
function adminPage() {
  document.body.addEventListener("click", async (e) => {
    const d = e.target.dataset;
    try {
      if (d.add) await showForm(d.add, null);
      else if (d.edit) {
        const [n, id] = d.edit.split(":");
        await showForm(
          n,
          rowsCache[n].find((r) => String(r.id) === id),
        );
      } else if (d.cancel) $("form-" + d.cancel).innerHTML = "";
      else if (d.del) {
        const [n, id] = d.del.split(":");
        if (!confirm("Delete this " + RESOURCES[n].title.toLowerCase() + "? This cannot be undone.")) return;
        await api(`${RESOURCES[n].url}/${id}`, { method: "DELETE" });
        showMessage("success", RESOURCES[n].title + " deleted.");
        await renderCrud(n);
      } else if (d.assign) {
        await api(`/complaints/${d.assign}/assign`, {
          method: "PUT",
          body: { officer_id: Number($("officer-" + d.assign).value) },
        });
        showMessage("success", "Complaint assigned.");
        await loadComplaints();
      } else if (d.reject) {
        const remarks = prompt("Reason for rejecting this complaint:");
        if (!remarks) return;
        await api(`/complaints/${d.reject}/status`, { method: "PUT", body: { status: "REJECTED", remarks } });
        showMessage("success", "Complaint rejected.");
        await loadComplaints();
      } else if (d.close) {
        await api(`/complaints/${d.close}/status`, {
          method: "PUT",
          body: { status: "CLOSED", remarks: "Closed by admin" },
        });
        showMessage("success", "Complaint closed.");
        await loadComplaints();
      }
    } catch (err) {
      showMessage("error", err.message);
    }
  });
  document.body.addEventListener("submit", async (e) => {
    if (!e.target.dataset.form) return;
    e.preventDefault();
    try {
      await saveForm(e.target);
    } catch (err) {
      showMessage("error", err.message);
    }
  });
  const loaders = { overview: loadOverview, complaints: loadComplaints, reports: loadReports };
  Object.keys(RESOURCES).forEach((n) => (loaders[n] = () => renderCrud(n)));
  initTabs(loaders);
}

initPage({ "admin-dashboard": adminPage });
