const result = JSON.parse(sessionStorage.getItem("secretScannerLastResult") || "null");
const escapeHtml = value => String(value || "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
function setText(id, value) { const el = document.getElementById(id); if (el) el.textContent = value; }
function render() {
  if (!result) { location.href = "index.html"; return; }
  const findings = result.findings || [];
  const critical = findings.filter(item => item.severity === "Critical").length;
  const high = findings.filter(item => item.severity === "High").length;
  setText("scoreNumber", result.score); setText("totalSecrets", result.total_found);
  setText("criticalCount", critical); setText("highCount", high); setText("mediumCount", result.total_found - critical - high);
  const status = document.querySelector(".score-status");
  if (status) status.textContent = result.total_found ? "REVIEW" : "SAFE";
  const list = document.getElementById("findingsList");
  list.innerHTML = findings.length ? findings.map(item => `<article class="finding-card ${item.severity.toLowerCase()}"><div class="finding-title">${escapeHtml(item.type)} exposed</div><div class="finding-path">Line ${item.line}: ${escapeHtml(item.preview)}</div><div class="severity-badge ${item.severity.toLowerCase()}">${escapeHtml(item.severity)}</div><p>${escapeHtml(item.fix)}</p></article>`).join("") : "<p>No secrets were detected in this scan.</p>";
}
document.addEventListener("DOMContentLoaded", () => {
  render();
  document.getElementById("themeToggle")?.addEventListener("click", () => document.body.classList.toggle("light-theme"));
  document.querySelector(".profile-btn")?.addEventListener("click", () => location.href = "profile.html");
  document.querySelector(".notification-btn")?.addEventListener("click", () => alert("There are no new notifications."));
});
