// public.js - pages anyone can open (no login needed).

async function loadStatsInto(containerId, full) {
  const s = (await api("/public/stats")).data;
  const cards = [
    [s.projects.total, "Total projects"],
    [s.projects.completed, "Completed projects"],
    [s.projects.ongoing, "Ongoing projects"],
    [s.complaints.total, "Total complaints"],
    [s.complaints.resolved, "Resolved complaints"],
    [s.contractors, "Contractors"],
  ];
  if (full) {
    cards.push(
      [s.roads.total, "Roads (" + s.roads.total_km + " km)"],
      [fmtMoney(s.projects.total_budget), "Total project budget"],
      [fmtMoney(s.expenditure_paid), "Amount paid so far"],
    );
  }
  $(containerId).innerHTML = cards
    .map(
      ([n, l]) =>
        `<div class="stat"><div class="num">${esc(n)}</div><div class="label">${esc(l)}</div></div>`,
    )
    .join("");
  return s;
}

async function homePage() {
  await loadStatsInto("stats", false);
  $("alerts").innerHTML = renderAlerts((await api("/alerts/public")).data);
}

async function transparencyPage() {
  const s = await loadStatsInto("stats", true);
  $("road-conditions").innerHTML = buildTable(
    [
      { label: "Road condition", render: (r) => badge(r.road_condition) },
      { label: "Number of roads", render: (r) => esc(r.total) },
    ],
    s.roads.by_condition,
  );
  const projects = (await api("/projects")).data;
  $("project-list").innerHTML = buildTable(
    [
      { label: "Project", render: (p) => esc(p.title) },
      { label: "Status", render: (p) => badge(p.status) },
      { label: "Budget", render: (p) => fmtMoney(p.budget) },
      { label: "Progress", render: (p) => progressBar(p.progress_percent) },
    ],
    projects,
  );
}

async function roadsPage() {
  const roads = (await api("/roads")).data;
  $("road-list").innerHTML = buildTable(
    [
      { label: "Road", render: (r) => esc(r.name) },
      { label: "Area", render: (r) => esc(r.area_name) + " (" + esc(r.ward) + ")" },
      { label: "Length (km)", render: (r) => esc(r.length_km) },
      { label: "Condition", render: (r) => badge(r.road_condition) },
      { label: "Last maintained", render: (r) => fmtDate(r.last_maintained_date) },
      { label: "", render: (r) => `<button class="btn small" data-road="${esc(r.id)}">Details</button>` },
    ],
    roads,
  );
  $("road-list").addEventListener("click", async (e) => {
    const id = e.target.dataset.road;
    if (!id) return;
    const r = (await api("/roads/" + id)).data;
    $("road-detail").innerHTML = `<div class="card"><h2>${esc(r.name)}</h2>
        <p>${esc(r.area_name)} (${esc(r.ward)}) | ${esc(r.length_km)} km | ${badge(r.road_condition)}</p>
        <h3>Projects on this road</h3>${buildTable(
          [
            { label: "Project", render: (p) => esc(p.title) },
            { label: "Status", render: (p) => badge(p.status) },
            { label: "Progress", render: (p) => progressBar(p.progress_percent) },
          ],
          r.projects,
          "No projects on this road.",
        )}
        <h3>Maintenance</h3>${buildTable(
          [
            { label: "Work", render: (m) => esc(m.description) },
            { label: "Status", render: (m) => badge(m.status) },
            { label: "Date", render: (m) => fmtDate(m.maintenance_date) },
          ],
          r.maintenance,
          "No maintenance records.",
        )}</div>`;
    $("road-detail").scrollIntoView({ behavior: "smooth" });
  });
}

async function projectsPage() {
  async function load() {
    const status = $("filter-status").value;
    const projects = (await api("/projects" + (status ? "?status=" + status : ""))).data;
    $("project-list").innerHTML = buildTable(
      [
        {
          label: "Project",
          render: (p) =>
            `<strong>${esc(p.title)}</strong><br><small>${esc(p.area_name)}${p.road_name ? " | " + esc(p.road_name) : ""}</small>`,
        },
        { label: "Status", render: (p) => badge(p.status) },
        { label: "Budget", render: (p) => fmtMoney(p.budget) },
        { label: "Contractor", render: (p) => esc(p.company_name || "Not assigned") },
        { label: "Expected completion", render: (p) => fmtDate(p.expected_completion_date) },
        { label: "Progress", render: (p) => progressBar(p.progress_percent) },
        {
          label: "",
          render: (p) => `<button class="btn small" data-project="${esc(p.id)}">History</button>`,
        },
      ],
      projects,
    );
  }
  $("filter-status").addEventListener("change", () => load().catch((e) => showMessage("error", e.message)));
  $("project-list").addEventListener("click", async (e) => {
    const id = e.target.dataset.project;
    if (!id) return;
    const rows = (await api("/progress/project/" + id)).data;
    $("progress-history").innerHTML =
      "<h2>Progress history</h2>" +
      buildTable(
        [
          { label: "Date", render: (r) => fmtDate(r.progress_date) },
          { label: "Progress", render: (r) => esc(r.progress_percent) + "%" },
          { label: "Remarks", render: (r) => esc(r.remarks) },
        ],
        rows,
        "No progress updates yet.",
      );
  });
  await load();
}

async function contractorsPage() {
  const rows = (await api("/contractors")).data;
  $("contractor-list").innerHTML = buildTable(
    [
      { label: "Company", render: (c) => esc(c.company_name) },
      { label: "License no.", render: (c) => esc(c.license_no) },
      { label: "Total projects", render: (c) => esc(c.total_projects) },
      { label: "Completed", render: (c) => esc(c.completed_projects) },
      { label: "Ongoing", render: (c) => esc(c.ongoing_projects) },
    ],
    rows,
  );
}

async function complaintStatusPage() {
  $("track-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    showMessage("info", "");
    $("track-result").innerHTML = "";
    const id = $("complaint-id").value.trim();
    if (!/^[0-9]+$/.test(id)) {
      showMessage("error", "Enter a valid complaint ID (numbers only).");
      return;
    }
    try {
      const c = (await api("/complaints/track/" + id)).data;
      $("track-result").innerHTML = `<div class="card"><h2>Complaint #${esc(c.id)}</h2>
        <p>Category: <strong>${esc(c.category)}</strong> | Area: ${esc(c.area_name)} | Date: ${fmtDate(c.complaint_date)}</p>
        <p>Current status: ${badge(c.status)}</p>
        <ul class="timeline">${c.history
          .map(
            (h) => `<li>${badge(h.new_status)}
        <small>${esc(h.changed_at)}</small></li>`,
          )
          .join("")}</ul></div>`;
    } catch (err) {
      showMessage("error", err.message);
    }
  });
}

initPage({
  home: homePage,
  transparency: transparencyPage,
  roads: roadsPage,
  projects: projectsPage,
  contractors: contractorsPage,
  "complaint-status": complaintStatusPage,
});
