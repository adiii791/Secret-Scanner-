const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:5001" : "";
const token = localStorage.getItem("secretScannerToken");
const api = async (path, options = {}) => {
  const response = await fetch(API_BASE + path, {...options, headers: {...options.headers, Authorization: "Bearer " + token}});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
};
function setProfile(user, scans) {
  const initials = user.name.split(" ").map(part => part[0]).join("").slice(0, 2).toUpperCase();
  document.getElementById("profileAvatar").textContent = initials;
  document.getElementById("heroName").textContent = user.name;
  document.getElementById("nameInput").value = user.name;
  const email = document.querySelector(".hero-meta span");
  if (email) {
    email.replaceChildren(document.createTextNode(user.email));
    email.prepend(Object.assign(document.createElement("i"), { className: "fa-regular fa-envelope" }));
    email.insertBefore(document.createTextNode(" "), email.lastChild);
  }
  const values = document.querySelectorAll(".stats b");
  if (values.length >= 3) {
    values[0].textContent = scans.length;
    values[1].textContent = scans.reduce((sum, scan) => sum + scan.total_found, 0);
    values[2].textContent = scans.length ? Math.round(scans.reduce((sum, scan) => sum + scan.score, 0) / scans.length) + "%" : "100%";
  }
}
document.addEventListener("DOMContentLoaded", async () => {
  if (!token) { location.href = "Login.html"; return; }
  try {
    const [me, history] = await Promise.all([api("/api/me"), api("/api/history")]);
    setProfile(me.user, history.scans);
  } catch (error) { localStorage.clear(); location.href = "Login.html"; return; }
  const inputs = [...document.querySelectorAll(".form-grid input")];
  const edit = () => { inputs[0].disabled = false; document.getElementById("saveRow").classList.add("show"); inputs[0].focus(); };
  document.getElementById("editBtn")?.addEventListener("click", edit);
  document.getElementById("editDetails")?.addEventListener("click", edit);
  document.getElementById("cancelBtn")?.addEventListener("click", () => { inputs[0].disabled = true; document.getElementById("saveRow").classList.remove("show"); });
  document.getElementById("saveBtn")?.addEventListener("click", async () => {
    try {
      const data = await api("/api/me", {method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify({name: inputs[0].value})});
      localStorage.setItem("secretScannerUser", JSON.stringify(data.user));
      document.getElementById("heroName").textContent = data.user.name;
      document.getElementById("profileAvatar").textContent = data.user.name.split(" ").map(part => part[0]).join("").slice(0, 2).toUpperCase();
      inputs[0].disabled = true; document.getElementById("saveRow").classList.remove("show");
    } catch (error) { alert(error.message); }
  });
  document.getElementById("logoutBtn").addEventListener("click", () => { localStorage.clear(); sessionStorage.removeItem("secretScannerLastResult"); location.href = "Login.html"; });
  document.getElementById("themeBtn").addEventListener("click", () => document.body.classList.toggle("light"));
  document.getElementById("avatarBtn").addEventListener("click", () => alert("Avatar uploads are not enabled yet."));
  document.getElementById("passwordBtn").addEventListener("click", async () => {
    const current_password = prompt("Enter your current password:");
    if (current_password === null) return;
    const new_password = prompt("Enter a new password (at least 6 characters):");
    if (new_password === null) return;
    try {
      await api("/api/me/password", {method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify({current_password, new_password})});
      alert("Password updated successfully.");
    } catch (error) { alert(error.message); }
  });
  document.getElementById("deleteBtn").addEventListener("click", async () => {
    if (!confirm("Delete your account and every saved scan? This cannot be undone.")) return;
    try {
      await api("/api/me", {method: "DELETE"});
      localStorage.clear(); location.href = "Login.html";
    } catch (error) { alert(error.message); }
  });
  document.querySelectorAll(".security-item .outline-btn, .connected .outline-btn, .card-head .small-btn:not(#editDetails)").forEach(button => {
    if (button.id === "passwordBtn") return;
    button.addEventListener("click", () => alert("This integration setting is ready for configuration in a future release."));
  });
});
