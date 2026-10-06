// api.js - single frontend gateway to the FastAPI backend.

const API_BASE = "http://localhost:8001";

// ---- login state ----
const Session = {
  getToken: () => localStorage.getItem("smc_token"),
  getUser: () => {
    try { return JSON.parse(localStorage.getItem("smc_user")); }
    catch (e) { return null; }
  },
  save(token, user) {
    localStorage.setItem("smc_token", token);
    localStorage.setItem("smc_user", JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem("smc_token");
    localStorage.removeItem("smc_user");
  },
};

// All supplied frontend pages use paths such as /complaints.
// The compatibility router exposes those paths under /api/ui.
async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = Session.getToken();
  if (token) headers["Authorization"] = "Bearer " + token;

  let response;
  try {
    response = await fetch(API_BASE + "/api/ui" + path, {
      method: options.method || "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
  } catch (e) {
    throw new Error("Cannot reach FastAPI. Start the backend on port 8001.");
  }

  let json = {};
  try { json = await response.json(); } catch (e) {}

  if (response.status === 401 && token && !options.noRedirect) {
    Session.clear();
    window.location.href = "/pages/login.html?expired=1";
    throw new Error("Session expired");
  }

  if (!response.ok || json.success === false) {
    throw new Error(json.detail || json.message || "Request failed (HTTP " + response.status + ")");
  }
  return json;
}
