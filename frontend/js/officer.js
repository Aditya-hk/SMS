// officer.js - officer dashboard (body has data-role="OFFICER").

async function loadComplaints() {
  const rows = (await api("/complaints")).data;
  $("complaint-list").innerHTML = buildTable(
    [
      { label: "ID", render: (c) => esc(c.id) },
      {
        label: "Title",
        render: (c) =>
          `<strong>${esc(c.title)}</strong><br><small>${esc(c.description).slice(0, 120)}</small>`,
      },
      { label: "Area", render: (c) => esc(c.area_name) },
      { label: "Date", render: (c) => fmtDate(c.complaint_date) },
      { label: "Status", render: (c) => badge(c.status) },
      {
        label: "Action",
        render: (c) =>
          c.status === "ASSIGNED"
            ? `<button class="btn small" data-act="IN_PROGRESS" data-id="${esc(c.id)}">Start work</button>`
            : c.status === "IN_PROGRESS"
              ? `<button class="btn small" data-act="RESOLVED" data-id="${esc(c.id)}">Mark resolved</button>`
              : "-",
      },
    ],
    rows,
    "No complaints are assigned to you.",
  );
}

async function loadProjects() {
  const rows = (await api("/projects/mine")).data;
  $("project-list").innerHTML = buildTable(
    [
      {
        label: "Project",
        render: (p) => `<strong>${esc(p.title)}</strong><br><small>${esc(p.area_name)}</small>`,
      },
      { label: "Status", render: (p) => badge(p.status) },
      { label: "Budget", render: (p) => fmtMoney(p.budget) },
      { label: "Contractor", render: (p) => esc(p.company_name || "-") },
      { label: "Progress", render: (p) => progressBar(p.progress_percent) },
      {
        label: "Action",
        render: (p) =>
          ["APPROVED", "IN_PROGRESS"].includes(p.status)
            ? `<div class="actions"><button class="btn small" data-progress="${esc(p.id)}">Update progress</button>
              ${
                p.status === "APPROVED"
                  ? `<button class="btn small secondary" data-pstatus="IN_PROGRESS"
           data-id="${esc(p.id)}">Start</button>`
                  : ""
              }
              <button class="btn small secondary" data-pstatus="COMPLETED" data-id="${esc(p.id)}">Complete</button></div>`
            : "-",
      },
    ],
    rows,
    "You do not manage any projects yet.",
  );
}

async function loadRoads() {
  $("road-list").innerHTML = buildTable(
    [
      { label: "Road", render: (r) => esc(r.name) },
      { label: "Area", render: (r) => esc(r.area_name) },
      { label: "Length (km)", render: (r) => esc(r.length_km) },
      { label: "Condition", render: (r) => badge(r.road_condition) },
      { label: "Last maintained", render: (r) => fmtDate(r.last_maintained_date) },
    ],
    (await api("/roads")).data,
  );
}

async function loadUtilities() {
  $("pipeline-list").innerHTML = buildTable(
    [
      { label: "Pipeline", render: (p) => esc(p.name) },
      { label: "Type", render: (p) => esc(p.pipeline_type) },
      { label: "Area", render: (p) => esc(p.area_name) },
      { label: "Length (km)", render: (p) => esc(p.length_km) },
      { label: "Status", render: (p) => badge(p.status) },
      { label: "Installed", render: (p) => esc(p.installed_year || "-") },
    ],
    (await api("/pipelines")).data,
  );
}

async function loadAlerts() {
  $("alert-list").innerHTML = renderAlerts((await api("/alerts")).data);
}

function officerPage() {
  document.body.addEventListener("click", async (e) => {
    const t = e.target;
    try {
      if (t.dataset.act) {
        // complaint status change
        const remarks =
          prompt(t.dataset.act === "RESOLVED" ? "What was done to resolve it?" : "Remarks (optional)") || "";
        await api(`/complaints/${t.dataset.id}/status`, {
          method: "PUT",
          body: { status: t.dataset.act, remarks },
        });
        showMessage("success", "Complaint updated.");
        await loadComplaints();
      } else if (t.dataset.progress) {
        // project progress
        const pct = prompt("New progress percentage (0-100):");
        if (pct === null) return;
        const remarks = prompt("Remarks (optional)") || "";
        await api("/progress", {
          method: "POST",
          body: { project_id: Number(t.dataset.progress), progress_percent: Number(pct), remarks },
        });
        showMessage("success", "Progress updated.");
        await loadProjects();
      } else if (t.dataset.pstatus) {
        // project status
        await api(`/projects/${t.dataset.id}/status`, { method: "PUT", body: { status: t.dataset.pstatus } });
        showMessage("success", "Project status updated.");
        await loadProjects();
      }
    } catch (err) {
      showMessage("error", err.message);
    }
  });
  initTabs({
    complaints: loadComplaints,
    projects: loadProjects,
    roads: loadRoads,
    utilities: loadUtilities,
    alerts: loadAlerts,
  });
}

initPage({ "officer-dashboard": officerPage });
