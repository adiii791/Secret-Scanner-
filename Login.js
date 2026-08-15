const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:5000" : "";
const panel = document.getElementById("panel");
const form = document.getElementById("authForm");
const submitBtn = document.getElementById("submitBtn");
const confirmInput = document.getElementById("confirm");
const nameInput = document.getElementById("name");

function showMessage(message, isError = true) {
  let messageEl = document.getElementById("authMessage");
  if (!messageEl) { messageEl = document.createElement("p"); messageEl.id = "authMessage"; form.append(messageEl); }
  messageEl.textContent = message;
  messageEl.style.color = isError ? "#d9534f" : "#22a06b";
}
function setMode(mode) {
  const isSignup = mode === "signup";
  panel.dataset.mode = mode;
  document.getElementById("tabLogin").classList.toggle("active", !isSignup);
  document.getElementById("tabSignup").classList.toggle("active", isSignup);
  document.getElementById("heading").textContent = isSignup ? "Create your account" : "Welcome back";
  document.getElementById("subheading").textContent = isSignup ? "Start your free workspace in under a minute." : "Log in to continue to your dashboard.";
  submitBtn.textContent = isSignup ? "Create account" : "Log in";
  confirmInput.required = isSignup; nameInput.required = isSignup;
  document.querySelectorAll(".login-only").forEach(el => el.style.display = isSignup ? "none" : "");
  document.querySelector(".signup-line").style.display = isSignup ? "block" : "none";
  showMessage("", false);
}
document.getElementById("tabLogin").addEventListener("click", () => setMode("login"));
document.getElementById("tabSignup").addEventListener("click", () => setMode("signup"));
document.getElementById("toSignup").addEventListener("click", () => setMode("signup"));
document.getElementById("toLogin").addEventListener("click", () => setMode("login"));
document.querySelectorAll(".social-btn").forEach(button => button.addEventListener("click", () => showMessage("Social sign-in is not configured for this workspace.")));
document.querySelector(".login-only a")?.addEventListener("click", event => { event.preventDefault(); showMessage("Password reset requires an email service, which is not configured yet."); });
form.addEventListener("submit", async event => {
  event.preventDefault();
  const signup = panel.dataset.mode === "signup";
  if (signup && confirmInput.value !== document.getElementById("password").value) return showMessage("Passwords do not match.");
  submitBtn.disabled = true; submitBtn.textContent = "Please wait…";
  try {
    const response = await fetch(API_BASE + (signup ? "/api/auth/register" : "/api/auth/login"), {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({name: nameInput.value.trim(), email: document.getElementById("email").value.trim(), password: document.getElementById("password").value})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Authentication failed.");
    localStorage.setItem("secretScannerToken", data.token);
    localStorage.setItem("secretScannerUser", JSON.stringify(data.user));
    location.href = "index.html";
  } catch (error) { showMessage(error.message); }
  finally { submitBtn.disabled = false; submitBtn.textContent = signup ? "Create account" : "Log in"; }
});
