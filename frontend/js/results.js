const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:5001" : "";
const token = localStorage.getItem("secretScannerToken");
const escapeHtml = value => String(value || "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));

function setText(id, value) { const el = document.getElementById(id); if (el) el.textContent = value; }

async function loadResult() {
  if (!token) { location.href = "Login.html"; return; }

  const stored = JSON.parse(sessionStorage.getItem("secretScannerLastResult") || "null");
  if (!stored) { location.href = "index.html"; return; }

  // Use the stored result directly if it has findings data (fresh scan result).
  // Fall back to re-fetching from the API only when we have an ID but no findings payload.
  let result = stored;
  if (result.findings === undefined) {
    const scanId = stored.scan_id || stored.id;
    if (!scanId) { location.href = "index.html"; return; }

    const response = await fetch(`${API_BASE}/api/scans/${scanId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.status === 401 || response.status === 422) {
      localStorage.clear();
      location.href = "Login.html";
      return;
    }

    if (!response.ok) {
      sessionStorage.removeItem("secretScannerLastResult");
      location.href = "index.html";
      return;
    }

    const json = await response.json();
    if (!json.scan) { location.href = "index.html"; return; }
    result = json.scan;
  }

  const findings = result.findings || [];
  const critical = findings.filter(item => item.severity === "Critical").length;
  const high = findings.filter(item => item.severity === "High").length;

  setText("scoreNumber", result.score);
  setText("totalSecrets", result.total_found);
  setText("criticalCount", critical);
  setText("highCount", high);
  setText("mediumCount", result.total_found - critical - high);

  const status = document.querySelector(".score-status");
  if (status) status.textContent = result.total_found ? "REVIEW" : "SAFE";

  const list = document.getElementById("findingsList");
  if (list) {
    list.innerHTML = findings.length
      ? findings.map(item => `
          <article class="finding-card ${item.severity.toLowerCase()}">
            <div class="finding-title">${escapeHtml(item.type)} exposed</div>
            <div class="finding-path">Line ${item.line}: ${escapeHtml(item.preview)}</div>
            <div class="severity-badge ${item.severity.toLowerCase()}">${escapeHtml(item.severity)}</div>
            <p>${escapeHtml(item.fix)}</p>
          </article>`).join("")
      : "<p>No secrets were detected in this scan.</p>";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadResult().catch(err => {
    console.error("loadResult error:", err);
    // Only redirect away if we have no stored result to show;
    // otherwise leave the page so the user sees an error rather than a silent redirect.
    if (!sessionStorage.getItem("secretScannerLastResult")) {
      location.href = "index.html";
    }
  });

  document.getElementById("themeToggle")?.addEventListener("click", () => {
    document.body.classList.toggle("light-theme");
  });

  document.querySelector(".profile-btn")?.addEventListener("click", () => {
    location.href = "profile.html";
  });

  document.querySelector(".notification-btn")?.addEventListener("click", () => {
    alert("There are no new notifications.");
  });

  document.getElementById("logoutBtn")?.addEventListener("click", () => {
    localStorage.clear();
    sessionStorage.removeItem("secretScannerLastResult");
    location.href = "Login.html";
  });
});
