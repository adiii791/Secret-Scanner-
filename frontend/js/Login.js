const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:5001" : "";
const panel = document.getElementById("panel");
const form = document.getElementById("authForm");
const submitBtn = document.getElementById("submitBtn");
const confirmInput = document.getElementById("confirm");
const nameInput = document.getElementById("name");
const phoneInput = document.getElementById("phone");
const otpInput = document.getElementById("otp");
const sendOtpBtn = document.getElementById("sendOtpBtn");

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidPhone(phone) {
  const digitsOnly = phone.replace(/\D/g, "");
  return digitsOnly.length >= 10 && digitsOnly.length <= 15 && /^\+?[0-9\s\-()]+$/.test(phone.trim());
}

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
  confirmInput.required = isSignup; nameInput.required = isSignup; phoneInput.required = isSignup; otpInput.required = isSignup;
  document.querySelectorAll(".login-only").forEach(el => el.style.display = isSignup ? "none" : "");
  document.querySelector(".signup-line").style.display = isSignup ? "block" : "none";
  showMessage("", false);
}

async function sendOtp() {
  const email = document.getElementById("email").value.trim();
  const phone = phoneInput.value.trim();

  if (!email) return showMessage("Please enter your email address first.");
  if (!isValidEmail(email)) return showMessage("Please enter a valid email address.");
  if (!phone) return showMessage("Please enter your phone number.");
  if (!isValidPhone(phone)) return showMessage("Please enter a valid phone number with at least 10 digits.");

  sendOtpBtn.disabled = true;
  sendOtpBtn.textContent = "Sending…";
  try {
    const response = await fetch(API_BASE + "/api/auth/request-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, phone })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not send OTP.");

    const otpValue = typeof data.otp === "string" && data.otp.trim() ? data.otp.trim() : "";
    const message = otpValue
      ? `${data.message || "OTP sent successfully"}. Your code is: ${otpValue}`
      : (data.message || "OTP sent. Check your email.");

    showMessage(message, false);
    otpInput.focus();
  } catch (error) {
    showMessage(error.message);
  } finally {
    sendOtpBtn.disabled = false;
    sendOtpBtn.textContent = "Send OTP";
  }
}

document.getElementById("tabLogin").addEventListener("click", () => setMode("login"));
document.getElementById("tabSignup").addEventListener("click", () => setMode("signup"));
document.getElementById("toSignup").addEventListener("click", () => setMode("signup"));
document.getElementById("toLogin").addEventListener("click", () => setMode("login"));
document.getElementById("sendOtpBtn").addEventListener("click", sendOtp);
form.addEventListener("submit", async event => {
  event.preventDefault();
  const signup = panel.dataset.mode === "signup";
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  if (!email || !isValidEmail(email)) return showMessage("Please enter a valid email address.");

  if (signup) {
    if (!nameInput.value.trim()) return showMessage("Please enter your full name.");
    if (confirmInput.value !== password) return showMessage("Passwords do not match.");
    if (password.length < 6) return showMessage("Password must be at least 6 characters.");
    if (!phoneInput.value.trim()) return showMessage("Phone number is required for signup.");
    if (!isValidPhone(phoneInput.value)) return showMessage("Please enter a valid phone number.");
    if (!otpInput.value.trim()) return showMessage("Request an OTP and enter the code before creating your account.");
  }

  submitBtn.disabled = true; submitBtn.textContent = "Please wait…";
  try {
    const response = await fetch(API_BASE + (signup ? "/api/auth/register" : "/api/auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: nameInput.value.trim(),
        email,
        phone: phoneInput.value.trim(),
        otp: otpInput.value.trim(),
        password
      })
    });
    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await response.json() : {};
    if (!response.ok && response.status >= 500) {
      throw new Error("The server could not complete login. Please restart the app and try again.");
    }
    if (!response.ok) throw new Error(data.error || "Authentication failed.");
    localStorage.setItem("secretScannerToken", data.token);
    localStorage.setItem("secretScannerUser", JSON.stringify(data.user));
    location.href = "index.html";
  } catch (error) { showMessage(error.message); }
  finally { submitBtn.disabled = false; submitBtn.textContent = signup ? "Create account" : "Log in"; }
});
