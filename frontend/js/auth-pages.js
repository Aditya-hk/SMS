// auth-pages.js - login and register pages.

async function loginPage() {
  const user = Session.getUser();
  if (user && Session.getToken()) {
    window.location.href = HOME_BY_ROLE[user.role];
    return;
  }
  if (queryParam("expired")) showMessage("info", "Your session expired. Please log in again.");

  $("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    showMessage("info", "");
    const email = $("email").value.trim();
    const password = $("password").value;
    if (!isEmail(email)) {
      showMessage("error", "Enter a valid email address.");
      return;
    }
    if (!password) {
      showMessage("error", "Enter your password.");
      return;
    }
    $("login-btn").disabled = true;
    try {
      const res = await api("/auth/login", { method: "POST", body: { email, password }, noRedirect: true });
      Session.save(res.data.token, res.data.user);
      window.location.href = HOME_BY_ROLE[res.data.user.role];
    } catch (err) {
      showMessage("error", err.message);
      $("login-btn").disabled = false;
    }
  });
}

async function registerPage() {
  $("register-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    showMessage("info", "");
    const body = {
      full_name: $("full_name").value.trim(),
      email: $("email").value.trim(),
      phone: $("phone").value.trim(),
      password: $("password").value,
      address: $("address").value.trim(),
      ward: $("ward").value.trim(),
    };
    if (body.full_name.length < 2) return showMessage("error", "Enter your full name.");
    if (!isEmail(body.email)) return showMessage("error", "Enter a valid email address.");
    if (body.phone && !isPhone(body.phone)) return showMessage("error", "Phone must be 10 to 13 digits.");
    if (!isStrongPassword(body.password))
      return showMessage(
        "error",
        "Password needs 8+ characters with an uppercase letter, a lowercase letter and a number.",
      );
    if (body.password !== $("confirm").value) return showMessage("error", "Passwords do not match.");
    try {
      await api("/auth/register", { method: "POST", body, noRedirect: true });
      showMessage("success", "Registration successful. Redirecting to login...");

      setTimeout(() => (window.location.href = "/pages/login.html"), 1500);
    } catch (err) {
      showMessage("error", err.message);
    }
  });
}

initPage({ login: loginPage, register: registerPage });
