// contractor.js - contractor dashboard (body has data-role="CONTRACTOR").

async function loadProjects() {
  const rows = (await api("/projects/mine")).data;
  $("project-list").innerHTML = buildTable(
    [
      {
        label: "Project",
        render: (p) =>
          `<strong>${esc(p.title)}</strong><br><small>${esc(p.area_name)}${p.road_name ? " | " + esc(p.road_name) : ""}</small>`,
      },
      { label: "Status", render: (p) => badge(p.status) },
      { label: "Budget", render: (p) => fmtMoney(p.budget) },
      { label: "Deadline", render: (p) => fmtDate(p.expected_completion_date) },
      { label: "Progress", render: (p) => progressBar(p.progress_percent) },
      {
        label: "Action",
        render: (p) =>
          ["APPROVED", "IN_PROGRESS"].includes(p.status)
            ? `<button class="btn small" data-progress="${esc(p.id)}">Update progress</button>`
            : "-",
      },
    ],
    rows,
    "No projects are assigned to you.",
  );
}

async function loadMaintenance() {
  const rows = (await api("/maintenance")).data;
  $("maintenance-list").innerHTML = buildTable(
    [
      { label: "Work", render: (m) => esc(m.description) },
      { label: "Location", render: (m) => esc(m.road_name || m.pipeline_name || "-") },
      { label: "Date", render: (m) => fmtDate(m.maintenance_date) },
      { label: "Status", render: (m) => badge(m.status) },
      {
        label: "Update status",
        render: (m) =>
          `<select data-maint="${esc(m.id)}">${["SCHEDULED", "IN_PROGRESS", "COMPLETED"]
            .map(
              (s) =>
                `<option value="${s}" ${s === m.status ? "selected" : ""}>${s.replace("_", " ")}</option>`,
            )
            .join("")}</select>`,
      },
    ],
    rows,
    "No maintenance work is assigned to you.",
  );
}

async function loadPayments() {
  const rows = (await api("/payments")).data;
  const paid = rows.filter((p) => p.status === "PAID").reduce((sum, p) => sum + p.amount, 0);
  $("payment-total").innerHTML =
    `<div class="stat"><div class="num">${fmtMoney(paid)}</div><div class="label">Total received</div></div>`;
  $("payment-list").innerHTML = buildTable(
    [
      { label: "Date", render: (p) => fmtDate(p.payment_date) },
      { label: "Project", render: (p) => esc(p.project_title) },
      { label: "Amount", render: (p) => fmtMoney(p.amount) },
      { label: "Status", render: (p) => badge(p.status) },
      { label: "Description", render: (p) => esc(p.description) },
    ],
    rows,
    "No payments yet.",
  );
}

function contractorPage() {
  document.body.addEventListener("click", async (e) => {
    const id = e.target.dataset.progress;
    if (!id) return;
    const pct = prompt("New progress percentage (0-100):");
    if (pct === null) return;
    const remarks = prompt("Remarks (optional)") || "";
    try {
      await api("/progress", {
        method: "POST",
        body: { project_id: Number(id), progress_percent: Number(pct), remarks },
      });
      showMessage("success", "Progress updated.");
      await loadProjects();
    } catch (err) {
      showMessage("error", err.message);
    }
  });
  document.body.addEventListener("change", async (e) => {
    const id = e.target.dataset.maint;
    if (!id) return;
    try {
      await api(`/maintenance/${id}/status`, { method: "PUT", body: { status: e.target.value } });
      showMessage("success", "Maintenance status updated.");
      await loadMaintenance();
    } catch (err) {
      showMessage("error", err.message);
    }
  });

  initTabs({ projects: loadProjects, maintenance: loadMaintenance, payments: loadPayments });
}

initPage({ "contractor-dashboard": contractorPage });
