const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:5000" : "";
const token = localStorage.getItem("secretScannerToken");
let latestScans = [];
let currentPage = 1;
const api = async (path, options = {}) => {
  const response = await fetch(API_BASE + path, {...options, headers: {...options.headers, Authorization: "Bearer " + token}});
  if (response.status === 401 || response.status === 422) { localStorage.clear(); location.href = "login.html"; throw new Error("Session expired."); }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
};
const escapeHtml = value => String(value || "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
function scanStatus(scan) { return scan.total_found === 0 ? ["safe", "Secure"] : scan.score < 50 ? ["critical", "Critical"] : ["warning", "Review"]; }
function renderHistory(scans) {
  latestScans = scans;
  const body = document.querySelector("#scanTable tbody");
  const footer = document.querySelector(".table-footer span");
  if (!body) return;
  const start = (currentPage - 1) * 10;
  body.innerHTML = scans.length ? scans.slice(start, start + 10).map(scan => {
    const [className, label] = scanStatus(scan);
    const time = new Date(scan.scanned_at).toLocaleString();
    return `<tr><td><div class="repo"><span class="repo-icon">⌘</span><div><b>Code scan</b><small>${escapeHtml(time)}</small></div></div></td><td>${escapeHtml(scan.input_type)}</td><td><b class="${scan.total_found ? "red-text" : ""}">${scan.total_found}</b></td><td><b>${scan.score}%</b></td><td><span class="badge ${className}">${label}</span></td><td><button class="row-action" data-scan-id="${scan.id}" title="Open result">•••</button></td></tr>`;
  }).join("") : "<tr><td colspan=\"6\">No scans yet. Paste code above to run your first scan.</td></tr>";
  if (footer) footer.textContent = `Showing ${Math.min(start + 1, scans.length)}–${Math.min(start + 10, scans.length)} of ${scans.length} scans`;
  const cards = document.querySelectorAll(".stats-grid .stat-card h2");
  if (cards.length >= 4) {
    const totalFindings = scans.reduce((total, scan) => total + scan.total_found, 0);
    cards[0].textContent = scans.length; cards[1].textContent = totalFindings;
    cards[2].textContent = "—";
    cards[3].textContent = scans.length ? Math.round(scans.reduce((total, scan) => total + scan.score, 0) / scans.length) + "%" : "100%";
  }
}
async function loadDashboard() {
  if (!token) { location.href = "login.html"; return; }
  const user = await api("/api/me");
  const name = user.user.name;
  document.querySelector(".welcome h1").innerHTML = `Good evening, ${escapeHtml(name.split(" ")[0])} <span>👋</span>`;
  document.querySelectorAll(".profile-text strong").forEach(el => el.textContent = name);
  document.querySelectorAll(".avatar").forEach(el => el.textContent = name.split(" ").map(part => part[0]).join("").slice(0, 2).toUpperCase());
  const history = await api("/api/history");
  renderHistory(history.scans);
}
document.addEventListener("DOMContentLoaded", () => {
  loadDashboard().catch(error => console.error(error));
  document.getElementById("scanForm")?.addEventListener("submit", async event => {
    event.preventDefault();
    const button = document.getElementById("scanSubmit"), message = document.getElementById("scanMessage");
    button.disabled = true; message.textContent = "Scanning…";
    try {
      const result = await api("/api/scan", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({code: document.getElementById("codeInput").value, input_type: "paste"})});
      sessionStorage.setItem("secretScannerLastResult", JSON.stringify(result));
      location.href = "results.html";
    } catch (error) { message.textContent = error.message; button.disabled = false; }
  });
  document.getElementById("logoutBtn")?.addEventListener("click", () => { localStorage.clear(); location.href = "login.html"; });
  document.getElementById("dropdownLogout")?.addEventListener("click", () => { localStorage.clear(); location.href = "login.html"; });
  const toggleTheme = () => document.body.classList.toggle("light");
  document.getElementById("themeBtn")?.addEventListener("click", toggleTheme);
  document.getElementById("dropdownTheme")?.addEventListener("click", toggleTheme);
  const profileButton = document.getElementById("profileBtn"), profileMenu = document.getElementById("profileDropdown");
  profileButton?.addEventListener("click", () => profileMenu.classList.toggle("open"));
  const notificationButton = document.getElementById("notificationBtn"), notificationPanel = document.getElementById("notificationPanel");
  notificationButton?.addEventListener("click", () => notificationPanel.classList.toggle("open"));
  document.getElementById("closeNotifications")?.addEventListener("click", () => notificationPanel.classList.remove("open"));
  document.getElementById("viewAllBtn")?.addEventListener("click", () => document.getElementById("history").scrollIntoView({behavior: "smooth"}));
  document.querySelector(".table-footer")?.addEventListener("click", event => {
    const button = event.target.closest("button");
    if (!button || !latestScans.length) return;
    const pages = Math.max(1, Math.ceil(latestScans.length / 10));
    const label = button.textContent.trim();
    currentPage = label === "‹" ? Math.max(1, currentPage - 1) : label === "›" ? Math.min(pages, currentPage + 1) : Math.min(pages, Math.max(1, Number(label) || currentPage));
    renderHistory(latestScans);
  });
  document.querySelector("#scanTable tbody")?.addEventListener("click", event => {
    const button = event.target.closest("[data-scan-id]");
    if (!button) return;
    const scan = latestScans.find(item => item.id === Number(button.dataset.scanId));
    if (scan) { sessionStorage.setItem("secretScannerLastResult", JSON.stringify(scan)); location.href = "results.html"; }
  });
  document.getElementById("exportBtn")?.addEventListener("click", () => {
    const csv = ["Date,Type,Findings,Score"].concat(latestScans.map(scan => [scan.scanned_at, scan.input_type, scan.total_found, scan.score].join(","))).join("\n");
    const download = document.createElement("a");
    download.href = URL.createObjectURL(new Blob([csv], {type: "text/csv"})); download.download = "secret-scanner-report.csv"; download.click();
    URL.revokeObjectURL(download.href);
  });
  document.querySelectorAll(".recommend-grid button").forEach(button => button.addEventListener("click", () => {
    const title = button.closest("article").querySelector("b").textContent;
    alert(title + ": review the recommendation and apply the change in your source repository.");
  }));
});
