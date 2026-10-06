// citizen.js - all citizen pages (body has data-role="CITIZEN").

async function citizenDashboard() {
  $("welcome").textContent = "Welcome, " + Session.getUser().full_name;
  const complaints = (await api("/complaints")).data;
  const count = (s) => complaints.filter((c) => c.status === s).length;
  const cards = [
    [complaints.length, "My complaints"],
    [count("SUBMITTED"), "Submitted"],
    [count("ASSIGNED") + count("IN_PROGRESS"), "Being handled"],
    [count("RESOLVED") + count("CLOSED"), "Resolved / closed"],
  ];
  $("stats").innerHTML = cards
    .map(([n, l]) => `<div class="stat"><div class="num">${n}</div><div class="label">${l}</div></div>`)
    .join("");
  $("alerts").innerHTML = renderAlerts((await api("/alerts/public")).data);
}

async function citizenProfile() {
  const me = (await api("/auth/me")).data;
  $("full_name").value = me.full_name || "";
  $("email").value = me.email || "";
  $("phone").value = me.phone || "";
  $("address").value = me.address || "";
  $("ward").value = me.ward || "";
  $("profile-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    showMessage("info", "");
    const body = {
      full_name: $("full_name").value.trim(),
      phone: $("phone").value.trim(),
      address: $("address").value.trim(),
      ward: $("ward").value.trim(),
    };
    if (body.full_name.length < 2) return showMessage("error", "Enter your full name.");
    if (body.phone && !isPhone(body.phone)) return showMessage("error", "Phone must be 10 to 13 digits.");
    try {
      await api("/auth/me", { method: "PUT", body });
      const user = Session.getUser();
      user.full_name = body.full_name;
      Session.save(Session.getToken(), user);
      renderHeader();
      showMessage("success", "Profile updated.");
    } catch (err) {
      showMessage("error", err.message);
    }
  });
}

async function submitComplaint() {
  await fillSelect("location_id", "/locations", (l) => `${l.area_name} (${l.ward})`);
  $("complaint_date").value = new Date().toISOString().slice(0, 10);
  $("complaint_date").max = $("complaint_date").value;
  $("complaint-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    showMessage("info", "");
    const body = {
      title: $("title").value.trim(),
      description: $("description").value.trim(),
      category: $("category").value,
      location_id: $("location_id").value,
      complaint_date: $("complaint_date").value,
    };
    if (body.title.length < 5) return showMessage("error", "Title must be at least 5 characters.");
    if (body.description.length < 10)
      return showMessage("error", "Description must be at least 10 characters.");
    if (!body.category) return showMessage("error", "Choose a category.");
    if (!body.location_id) return showMessage("error", "Choose a location.");
    try {
      const res = await api("/complaints", { method: "POST", body });
      window.location.href = "/pages/citizen/complaint-details.html?id=" + res.data.id;
    } catch (err) {
      showMessage("error", err.message);
    }
  });
}

async function myComplaints() {
  async function load() {
    const status = $("filter-status").value;
    const rows = (await api("/complaints" + (status ? "?status=" + status : ""))).data;
    $("complaint-list").innerHTML = buildTable(
      [
        { label: "ID", render: (c) => esc(c.id) },
        { label: "Title", render: (c) => esc(c.title) },
        { label: "Category", render: (c) => esc(c.category) },
        { label: "Date", render: (c) => fmtDate(c.complaint_date) },
        { label: "Status", render: (c) => badge(c.status) },
        {
          label: "",
          render: (c) =>
            `<a class="btn small" href="/pages/citizen/complaint-details.html?id=${esc(c.id)}">View</a>`,
        },
      ],
      rows,
      "You have not submitted any complaints yet.",
    );
  }
  $("filter-status").addEventListener("change", () => load().catch((e) => showMessage("error", e.message)));
  await load();
}

async function complaintDetails() {
  const id = queryParam("id");
  if (!id) return showMessage("error", "No complaint ID given.");
  let rating = 0;

  async function load() {
    const c = (await api("/complaints/" + id)).data;
    let html = `<div class="card"><h2>#${esc(c.id)} ${esc(c.title)}</h2>
        <p>${badge(c.status)} | ${esc(c.category)} | ${esc(c.area_name)} (${esc(c.ward)}) | ${fmtDate(c.complaint_date)}</p>
        <p>${esc(c.description)}</p><p>Assigned officer: <strong>${esc(c.officer_name || "Not yet assigned")}</strong></p>`;

    if (c.status === "RESOLVED")
      html += `<button class="btn" id="close-btn">Confirm resolved and close complaint</button>`;
    html +=
      `</div><h2>Status history</h2><ul class="timeline">` +
      c.history
        .map(
          (h) =>
            `<li>${badge(h.new_status)} by ${esc(h.changed_by_name)} <small>${esc(h.changed_at)}</small><br>${esc(h.remarks)}</li>`,
        )
        .join("") +
      "</ul>";
    if (c.feedback) {
      html += `<div class="card"><h2>Your feedback</h2><p>Rating: ${"&#9733;".repeat(c.feedback.rating)}
          (${c.feedback.rating}/5)</p><p>${esc(c.feedback.comment)}</p></div>`;
    } else if (["RESOLVED", "CLOSED"].includes(c.status)) {
      html += `<div class="card form-narrow"><h2>Give feedback</h2><form id="feedback-form">
          <label>Rating</label><div class="stars" id="stars">${[1, 2, 3, 4, 5]
            .map(
              (n) => `<button type="button"
          data-n="${n}">&#9733;</button>`,
            )
            .join("")}</div>
          <label for="comment">Comment (optional)</label><textarea id="comment" maxlength="500"></textarea>
          <br><button class="btn" type="submit">Submit feedback</button></form></div>`;
    }
    $("details").innerHTML = html;

    const closeBtn = $("close-btn");
    if (closeBtn)
      closeBtn.addEventListener("click", async () => {
        try {
          await api(`/complaints/${id}/status`, {
            method: "PUT",
            body: { status: "CLOSED", remarks: "Closed by citizen" },
          });
          await load();
          showMessage("success", "Complaint closed.");
        } catch (err) {
          showMessage("error", err.message);
        }
      });
    const stars = $("stars");
    if (stars) {
      stars.addEventListener("click", (e) => {
        if (!e.target.dataset.n) return;
        rating = Number(e.target.dataset.n);
        stars
          .querySelectorAll("button")
          .forEach((b) => b.classList.toggle("on", Number(b.dataset.n) <= rating));
      });
      $("feedback-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        if (rating < 1) return showMessage("error", "Please choose a rating from 1 to 5 stars.");
        try {
          await api("/feedback", {
            method: "POST",
            body: { complaint_id: Number(id), rating, comment: $("comment").value.trim() },
          });
          await load();
          showMessage("success", "Thank you for your feedback.");
        } catch (err) {
          showMessage("error", err.message);
        }
      });
    }
  }
  await load();
}

initPage({
  "citizen-dashboard": citizenDashboard,
  "citizen-profile": citizenProfile,
  "submit-complaint": submitComplaint,
  "my-complaints": myComplaints,
  "complaint-details": complaintDetails,
});
