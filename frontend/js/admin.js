const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:5001" : "";
const escapeHtml = value => String(value || "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
async function loadDatabase() {
  const token = localStorage.getItem("secretScannerToken");
  const response = await fetch(API_BASE + "/api/admin/database", {headers: {Authorization: "Bearer " + token}});
  const data = await response.json();
  if (!response.ok) {
    document.getElementById("adminStatus").textContent = data.error || "Access denied.";
    document.getElementById("refreshBtn").hidden = true;
    return;
  }
  document.getElementById("adminStatus").textContent = "Administrator access verified. Showing up to 200 newest scans.";
  document.getElementById("userCount").textContent = data.summary.users;
  document.getElementById("scanCount").textContent = data.summary.scans;
  document.getElementById("usersBody").innerHTML = data.users.map(user => `<tr><td>${user.id}</td><td>${escapeHtml(user.name)}</td><td>${escapeHtml(user.email)}</td><td>${new Date(user.created_at).toLocaleString()}</td></tr>`).join("") || "<tr><td colspan='4'>No users found.</td></tr>";
  document.getElementById("scansBody").innerHTML = data.scans.map(scan => `<tr><td>${escapeHtml(scan.user_email)}</td><td>${escapeHtml(scan.input_type)}</td><td>${scan.total_found}</td><td>${scan.score}%</td><td>${new Date(scan.scanned_at).toLocaleString()}</td><td>${escapeHtml(scan.code_snippet)}</td></tr>`).join("") || "<tr><td colspan='6'>No scans found.</td></tr>";
}
document.getElementById("refreshBtn").addEventListener("click", loadDatabase);
loadDatabase();
