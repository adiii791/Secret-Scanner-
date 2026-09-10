const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:5001" : "";
const token = localStorage.getItem("secretScannerToken");

const api = async (path, options = {}) => {
  const response = await fetch(API_BASE + path, {
    ...options,
    headers: { ...options.headers, Authorization: "Bearer " + token },
  });
  if (response.status === 401 || response.status === 422) {
    localStorage.clear();
    location.href = "Login.html";
    throw new Error("Session expired.");
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
};

function setProfile(user, scans) {
  const initials = user.name.split(" ").map(p => p[0]).join("").slice(0, 2).toUpperCase();
  document.getElementById("profileAvatar").textContent = initials;
  document.getElementById("heroName").textContent = user.name;

  // hero role — mark admins
  const roleEl = document.getElementById("heroRole");
  if (roleEl) roleEl.textContent = (user.is_admin ? "Administrator" : "Member") + " • Secret Scanner Workspace";

  // hero email
  const heroEmail = document.getElementById("heroEmail");
  if (heroEmail) heroEmail.innerHTML = `<i class="fa-regular fa-envelope"></i> ${user.email}`;

  // hero joined date
  const heroJoined = document.getElementById("heroJoined");
  if (heroJoined && user.created_at) {
    const joined = new Date(user.created_at).toLocaleDateString(undefined, { month: "long", year: "numeric" });
    heroJoined.innerHTML = `<i class="fa-regular fa-calendar"></i> Joined ${joined}`;
  }

  // form grid fields
  document.getElementById("nameInput").value = user.name;
  const emailInput = document.getElementById("emailInput");
  if (emailInput) emailInput.value = user.email;
  const roleInput = document.getElementById("roleInput");
  if (roleInput) roleInput.value = user.is_admin ? "Administrator" : "Member";
  const joinedInput = document.getElementById("joinedInput");
  if (joinedInput && user.created_at) {
    joinedInput.value = new Date(user.created_at).toLocaleDateString();
  }

  // stats from scan history
  const totalFindings = scans.reduce((sum, s) => sum + s.total_found, 0);
  const avgScore = scans.length
    ? Math.round(scans.reduce((sum, s) => sum + s.score, 0) / scans.length)
    : 100;

  const statScans = document.getElementById("statScans");
  const statFindings = document.getElementById("statFindings");
  const statScore = document.getElementById("statScore");
  if (statScans) statScans.textContent = scans.length;
  if (statFindings) statFindings.textContent = totalFindings;
  if (statScore) statScore.textContent = avgScore + "%";

  // activity list — show last 3 scans
  const activityList = document.getElementById("activityList");
  if (activityList) {
    if (!scans.length) {
      activityList.innerHTML = "<li><i class='fa-solid fa-radar'></i><div><b>No scans yet</b><p>Run your first scan from the dashboard.</p></div><span></span></li>";
    } else {
      const recent = scans.slice(0, 3);
      activityList.innerHTML = recent.map(scan => {
        const time = new Date(scan.scanned_at).toLocaleString();
        const icon = scan.total_found ? "fa-triangle-exclamation orange-text" : "fa-shield-check green-text";
        const label = scan.total_found ? `${scan.total_found} secret${scan.total_found > 1 ? "s" : ""} found` : "Secure";
        return `<li><i class="fa-solid ${icon}"></i><div><b>Code scan (${scan.input_type})</b><p>${time}</p></div><span>${scan.score}%</span></li>`;
      }).join("");
    }
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!token) { location.href = "Login.html"; return; }

  let user, scans;
  try {
    const [me, history] = await Promise.all([api("/api/me"), api("/api/history")]);
    user = me.user;
    user.is_admin = me.is_admin;
    scans = history.scans || [];
    setProfile(user, scans);
  } catch (error) {
    // 401 already handled inside api(); only reach here for other errors
    console.error(error);
    return;
  }

  const inputs = [...document.querySelectorAll(".form-grid input")];
  const nameInput = document.getElementById("nameInput");

  function enableEdit() {
    nameInput.disabled = false;
    document.getElementById("saveRow").classList.add("show");
    nameInput.focus();
  }

  document.getElementById("editBtn")?.addEventListener("click", enableEdit);
  document.getElementById("editDetails")?.addEventListener("click", enableEdit);

  document.getElementById("cancelBtn")?.addEventListener("click", () => {
    nameInput.value = user.name;
    nameInput.disabled = true;
    document.getElementById("saveRow").classList.remove("show");
  });

  document.getElementById("saveBtn")?.addEventListener("click", async () => {
    try {
      const data = await api("/api/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: nameInput.value }),
      });
      user = { ...user, ...data.user };
      localStorage.setItem("secretScannerUser", JSON.stringify(data.user));
      document.getElementById("heroName").textContent = data.user.name;
      const initials = data.user.name.split(" ").map(p => p[0]).join("").slice(0, 2).toUpperCase();
      document.getElementById("profileAvatar").textContent = initials;
      nameInput.disabled = true;
      document.getElementById("saveRow").classList.remove("show");
    } catch (error) { alert(error.message); }
  });

  document.getElementById("logoutBtn").addEventListener("click", () => {
    localStorage.clear();
    sessionStorage.removeItem("secretScannerLastResult");
    location.href = "Login.html";
  });

  document.getElementById("themeBtn").addEventListener("click", () => {
    const isLight = document.body.classList.toggle("light");
    document.getElementById("themeBtn").innerHTML = isLight
      ? '<i class="fa-solid fa-sun"></i> Light mode'
      : '<i class="fa-solid fa-moon"></i> Dark mode';
  });

  document.getElementById("avatarBtn").addEventListener("click", () => {
    alert("Avatar uploads are not enabled yet.");
  });

  document.getElementById("passwordBtn").addEventListener("click", async () => {
    const current_password = prompt("Enter your current password:");
    if (current_password === null) return;
    const new_password = prompt("Enter a new password (at least 6 characters):");
    if (new_password === null) return;
    try {
      await api("/api/me/password", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password, new_password }),
      });
      alert("Password updated successfully.");
    } catch (error) { alert(error.message); }
  });

  document.getElementById("deleteBtn").addEventListener("click", async () => {
    if (!confirm("Delete your account and every saved scan? This cannot be undone.")) return;
    try {
      await api("/api/me", { method: "DELETE" });
      localStorage.clear();
      location.href = "Login.html";
    } catch (error) { alert(error.message); }
  });

  document.querySelectorAll(".security-item .outline-btn, .connected .outline-btn, .card-head .small-btn:not(#editDetails)").forEach(button => {
    if (button.id === "passwordBtn") return;
    button.addEventListener("click", () => alert("This integration setting is ready for configuration in a future release."));
  });
});
