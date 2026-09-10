const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:5001" : "";
const panel = document.getElementById("panel");
const form = document.getElementById("authForm");
const submitBtn = document.getElementById("submitBtn");
const confirmInput = document.getElementById("confirm");
const nameInput = document.getElementById("name");
const phoneInput = document.getElementById("phone");
const otpInput = document.getElementById("otp");
const sendOtpBtn = document.getElementById("sendOtpBtn");

// ── Social OAuth provider config ─────────────────────────────────────────────
const OAUTH_PROVIDERS = {
  google:   { name: "Google",   url: "https://accounts.google.com/o/oauth2/v2/auth", note: "Sign in with your Google account, then return here to continue." },
  facebook: { name: "Facebook", url: "https://www.facebook.com/v19.0/dialog/oauth",  note: "Sign in with your Facebook account, then return here to continue." },
  github:   { name: "GitHub",   url: "https://github.com/login/oauth/authorize",      note: "Authorise with your GitHub account, then return here to continue." },
};

// ── Helpers ───────────────────────────────────────────────────────────────────
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidPhone(phone) {
  const digits = phone.replace(/\D/g, "");
  return digits.length >= 10 && digits.length <= 15 && /^\+?[0-9\s\-()]+$/.test(phone.trim());
}

function showMessage(message, isError = true) {
  let el = document.getElementById("authMessage");
  if (!el) {
    el = document.createElement("p");
    el.id = "authMessage";
    el.style.cssText = "margin-top:10px;font-size:13px;text-align:center;";
    form.append(el);
  }
  el.textContent = message;
  el.style.color = isError ? "#d9534f" : "#22a06b";
}

// ── Mode toggle ───────────────────────────────────────────────────────────────
function setMode(mode) {
  const isSignup = mode === "signup";
  panel.dataset.mode = mode;
  document.getElementById("tabLogin").classList.toggle("active", !isSignup);
  document.getElementById("tabSignup").classList.toggle("active", isSignup);
  document.getElementById("heading").textContent = isSignup ? "Create your account" : "Welcome back";
  document.getElementById("subheading").textContent = isSignup
    ? "Start your free workspace in under a minute."
    : "Log in to continue to your dashboard.";
  submitBtn.textContent = isSignup ? "Create account" : "Log in";
  confirmInput.required = isSignup;
  nameInput.required = isSignup;
  // phone & otp are always optional – do NOT set required
  phoneInput.required = false;
  otpInput.required = false;
  document.querySelectorAll(".login-only").forEach(el => el.style.display = isSignup ? "none" : "");
  document.querySelector(".signup-line").style.display = isSignup ? "block" : "none";
  showMessage("", false);
}

// ── OTP send ──────────────────────────────────────────────────────────────────
async function sendOtp() {
  const email = document.getElementById("email").value.trim();
  const phone = phoneInput.value.trim();

  if (!email) return showMessage("Please enter your email address first.");
  if (!isValidEmail(email)) return showMessage("Please enter a valid email address.");
  if (!phone) return showMessage("Please enter your phone number to request an OTP.");
  if (!isValidPhone(phone)) return showMessage("Please enter a valid phone number (at least 10 digits).");

  sendOtpBtn.disabled = true;
  sendOtpBtn.textContent = "Sending…";
  try {
    const response = await fetch(API_BASE + "/api/auth/request-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, phone }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not send OTP.");

    const otpValue = typeof data.otp === "string" && data.otp.trim() ? data.otp.trim() : "";
    const message = otpValue
      ? `${data.message || "OTP sent"}. Your code: ${otpValue}`
      : (data.message || "OTP sent — check your email/SMS.");
    showMessage(message, false);
    otpInput.focus();
  } catch (error) {
    showMessage(error.message);
  } finally {
    sendOtpBtn.disabled = false;
    sendOtpBtn.textContent = "Send OTP";
  }
}

// ── Social sign-in modal ──────────────────────────────────────────────────────
function openOauthModal(providerKey) {
  const provider = OAUTH_PROVIDERS[providerKey];
  if (!provider) return;

  const modal = document.getElementById("oauthModal");
  document.getElementById("oauthTitle").textContent = `Continue with ${provider.name}`;
  document.getElementById("oauthMessage").textContent = provider.note;
  document.getElementById("oauthProviderName").textContent = provider.name;
  document.getElementById("oauthContinueBtn").href = provider.url;
  modal.hidden = false;
  document.getElementById("oauthCloseBtn").focus();
}

function closeOauthModal() {
  document.getElementById("oauthModal").hidden = true;
}

// ── Event listeners ───────────────────────────────────────────────────────────
document.getElementById("tabLogin").addEventListener("click", () => setMode("login"));
document.getElementById("tabSignup").addEventListener("click", () => setMode("signup"));
document.getElementById("toSignup").addEventListener("click", () => setMode("signup"));
document.getElementById("toLogin").addEventListener("click", () => setMode("login"));
sendOtpBtn.addEventListener("click", sendOtp);

document.getElementById("googleBtn").addEventListener("click", () => openOauthModal("google"));
document.getElementById("facebookBtn").addEventListener("click", () => openOauthModal("facebook"));
document.getElementById("githubBtn").addEventListener("click", () => openOauthModal("github"));
document.getElementById("oauthCloseBtn").addEventListener("click", closeOauthModal);

// Close modal on backdrop click
document.getElementById("oauthModal").addEventListener("click", event => {
  if (event.target === event.currentTarget) closeOauthModal();
});

// Close modal on Escape
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && !document.getElementById("oauthModal").hidden) closeOauthModal();
});

// Forgot password
document.getElementById("forgotPasswordLink").addEventListener("click", event => {
  event.preventDefault();
  showMessage("Password reset: use the email you registered with and contact support, or create a new account.", false);
});

// ── Form submit ───────────────────────────────────────────────────────────────
form.addEventListener("submit", async event => {
  event.preventDefault();
  const isSignup = panel.dataset.mode === "signup";
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  if (!email || !isValidEmail(email)) return showMessage("Please enter a valid email address.");

  if (isSignup) {
    if (!nameInput.value.trim()) return showMessage("Please enter your full name.");
    if (confirmInput.value !== password) return showMessage("Passwords do not match.");
    if (password.length < 6) return showMessage("Password must be at least 6 characters.");
    // phone & OTP are optional — only validate if user filled them in
    if (phoneInput.value.trim() && !isValidPhone(phoneInput.value)) {
      return showMessage("Please enter a valid phone number or leave it blank.");
    }
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Please wait…";
  try {
    const body = {
      name: nameInput.value.trim(),
      email,
      password,
    };
    // include optional fields only when present
    if (phoneInput.value.trim()) body.phone = phoneInput.value.trim();
    if (otpInput.value.trim()) body.otp = otpInput.value.trim();

    const response = await fetch(API_BASE + (isSignup ? "/api/auth/register" : "/api/auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await response.json() : {};

    if (!response.ok && response.status >= 500) {
      throw new Error("Server error. Please try again later.");
    }
    if (!response.ok) throw new Error(data.error || "Authentication failed.");

    localStorage.setItem("secretScannerToken", data.token);
    localStorage.setItem("secretScannerUser", JSON.stringify(data.user));

    // honour "remember me" — if unchecked, clear on browser close via sessionStorage flag
    if (!document.getElementById("rememberMe")?.checked) {
      sessionStorage.setItem("secretScannerSessionOnly", "1");
    }

    location.href = "index.html";
  } catch (error) {
    showMessage(error.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = isSignup ? "Create account" : "Log in";
  }
});
