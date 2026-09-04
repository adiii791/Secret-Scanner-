const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:5001" : "";
const token = localStorage.getItem("secretScannerToken");
let latestScans = [];
let allScans = [];
let currentPage = 1;

const api = async (path, options = {}) => {
  const response = await fetch(API_BASE + path, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: "Bearer " + token,
    },
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

const escapeHtml = value => String(value || "").replace(/[&<>"']/g, char => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
}[char]));

function scanStatus(scan) {
  return scan.total_found === 0 ? ["safe", "Secure"] : scan.score < 50 ? ["critical", "Critical"] : ["warning", "Review"];
}

function renderHistory(scans) {
  latestScans = scans;
  const body = document.querySelector("#scanTable tbody");
  const footer = document.querySelector(".table-footer span");
  if (!body) return;

  const start = (currentPage - 1) * 10;
  const pageItems = scans.slice(start, start + 10);

  body.innerHTML = scans.length
    ? pageItems.map(scan => {
        const [className, label] = scanStatus(scan);
        const time = new Date(scan.scanned_at).toLocaleString();
        return `<tr><td><div class="repo"><span class="repo-icon">⌘</span><div><b>Code scan</b><small>${escapeHtml(time)}</small></div></div></td><td>${escapeHtml(scan.input_type)}</td><td><b class="${scan.total_found ? "red-text" : ""}">${scan.total_found}</b></td><td><b>${scan.score}%</b></td><td><span class="badge ${className}">${label}</span></td><td><button class="row-action" data-scan-id="${scan.id}" title="Open result">•••</button></td></tr>`;
      }).join("")
    : "<tr><td colspan=\"6\">No scans yet. Paste code above to run your first scan.</td></tr>";

  if (footer) {
    const total = scans.length || 0;
    const from = total ? start + 1 : 0;
    const to = Math.min(start + 10, total);
    footer.textContent = total ? `Showing ${from}–${to} of ${total} scans` : "Showing 0 of 0 scans";
  }

  const cards = document.querySelectorAll(".stats-grid .stat-card h2");
  if (cards.length >= 4) {
    const totalFindings = scans.reduce((total, scan) => total + scan.total_found, 0);
    cards[0].textContent = scans.length;
    cards[1].textContent = totalFindings;
    cards[2].textContent = scans.length ? "12" : "0";
    cards[3].textContent = scans.length ? Math.round(scans.reduce((total, scan) => total + scan.score, 0) / scans.length) + "%" : "100%";
  }
}

function createCharts(scans = []) {
  if (typeof Chart === "undefined") return;

  const scores = scans.length ? scans.map(scan => scan.score) : [100];
  const averageScore = Math.round(scores.reduce((total, score) => total + score, 0) / scores.length);
  const scoreCtx = document.getElementById("scoreChart");
  const weeklyCtx = document.getElementById("weeklyChart");
  const secretCtx = document.getElementById("secretChart");

  if (scoreCtx) {
    new Chart(scoreCtx, {
      type: "doughnut",
      data: { datasets: [{ data: [averageScore, 100 - averageScore], backgroundColor: ["#28d17c", "#263247"], borderWidth: 0 }] },
      options: { cutout: "78%", responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { enabled: false } } },
    });
    const score = document.querySelector(".score-center strong");
    if (score) score.textContent = averageScore;
  }

  if (weeklyCtx) {
    const today = new Date();
    const weeklyCounts = Array.from({ length: 7 }, (_, index) => {
      const date = new Date(today);
      date.setHours(0, 0, 0, 0);
      date.setDate(today.getDate() - (6 - index));
      return scans.filter(scan => {
        const scannedAt = new Date(scan.scanned_at);
        return scannedAt >= date && scannedAt < new Date(date.getTime() + 86400000);
      }).length;
    });
    new Chart(weeklyCtx, {
      type: "line",
      data: {
        labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        datasets: [{
          label: "Scans",
          data: weeklyCounts,
          borderColor: "#36a3ff",
          backgroundColor: "rgba(54, 163, 255, 0.18)",
          borderWidth: 3,
          tension: 0.35,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, ticks: { precision: 0 } },
        },
      },
    });
  }

  if (secretCtx) {
    const typeCounts = scans.reduce((counts, scan) => {
      (scan.findings || []).forEach(finding => {
        counts[finding.type] = (counts[finding.type] || 0) + 1;
      });
      return counts;
    }, {});
    const typeEntries = Object.entries(typeCounts).sort((first, second) => second[1] - first[1]).slice(0, 4);
    new Chart(secretCtx, {
      type: "doughnut",
      data: {
        labels: typeEntries.length ? typeEntries.map(entry => entry[0]) : ["No findings"],
        datasets: [{
          data: typeEntries.length ? typeEntries.map(entry => entry[1]) : [1],
          backgroundColor: ["#ff5d73", "#ffad42", "#36a3ff", "#28d17c"],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
      },
    });
  }
}

function applyTheme(isLight) {
  document.body.classList.toggle("light", isLight);
  const themeBtn = document.getElementById("themeBtn");
  if (themeBtn) {
    themeBtn.innerHTML = isLight
      ? '<i class="fa-solid fa-sun"></i><span>Light mode</span>'
      : '<i class="fa-solid fa-moon"></i><span>Dark mode</span>';
  }
}

async function loadDashboard() {
  if (!token) { location.href = "Login.html"; return; }

  try {
    const user = await api("/api/me");
    const name = user.user.name;
    const greeting = document.querySelector(".welcome h1");
    if (greeting) greeting.innerHTML = `Good evening, ${escapeHtml(name.split(" ")[0])} <span>👋</span>`;

    document.querySelectorAll(".profile-text strong").forEach(el => el.textContent = name);
    document.querySelectorAll(".avatar").forEach(el => {
      const initials = name.split(" ").map(part => part[0]).join("").slice(0, 2).toUpperCase();
      el.textContent = initials;
    });

    const history = await api("/api/history");
    allScans = history.scans || [];
    renderHistory(allScans);
    createCharts(allScans);
  } catch (error) {
    console.error(error);
    allScans = [];
    renderHistory([]);
    const message = document.getElementById("scanMessage");
    if (message) message.textContent = "Unable to load your dashboard. Please refresh and try again.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(document.body.classList.contains("light"));
  loadDashboard().catch(error => console.error(error));

  const searchInput = document.getElementById("searchInput");
  searchInput?.addEventListener("input", event => {
    const query = event.target.value.trim().toLowerCase();
    const filtered = allScans.filter(scan => {
      const text = `${scan.input_type} ${scan.total_found} ${scan.score} ${scan.scanned_at || ""}`.toLowerCase();
      return !query || text.includes(query);
    });
    currentPage = 1;
    renderHistory(filtered);
  });

  document.getElementById("scanForm")?.addEventListener("submit", async event => {
    event.preventDefault();
    const button = document.getElementById("scanSubmit");
    const message = document.getElementById("scanMessage");
    button.disabled = true;
    message.textContent = "Scanning…";
    try {
      const result = await api("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: document.getElementById("codeInput").value, input_type: "paste" }),
      });
      sessionStorage.setItem("secretScannerLastResult", JSON.stringify(result));
      location.href = "results.html";
    } catch (error) {
      message.textContent = error.message;
      button.disabled = false;
    }
  });

  document.getElementById("logoutBtn")?.addEventListener("click", () => {
    localStorage.clear();
    sessionStorage.removeItem("secretScannerLastResult");
    location.href = "Login.html";
  });

  document.getElementById("dropdownLogout")?.addEventListener("click", () => {
    localStorage.clear();
    sessionStorage.removeItem("secretScannerLastResult");
    location.href = "Login.html";
  });

  const toggleTheme = () => {
    const isLight = !document.body.classList.contains("light");
    applyTheme(isLight);
  };

  document.getElementById("themeBtn")?.addEventListener("click", toggleTheme);
  document.getElementById("dropdownTheme")?.addEventListener("click", toggleTheme);

  const profileButton = document.getElementById("profileBtn");
  const profileMenu = document.getElementById("profileDropdown");
  profileButton?.addEventListener("click", event => {
    event.stopPropagation();
    if (profileMenu) profileMenu.classList.toggle("open");
  });

  const notificationButton = document.getElementById("notificationBtn");
  const notificationPanel = document.getElementById("notificationPanel");
  notificationButton?.addEventListener("click", event => {
    event.stopPropagation();
    if (notificationPanel) notificationPanel.classList.toggle("open");
  });

  document.getElementById("closeNotifications")?.addEventListener("click", () => {
    if (notificationPanel) notificationPanel.classList.remove("open");
  });

  document.addEventListener("click", event => {
    if (!event.target.closest("#profileBtn") && !event.target.closest("#profileDropdown")) {
      if (profileMenu) profileMenu.classList.remove("open");
    }
    if (!event.target.closest("#notificationBtn") && !event.target.closest("#notificationPanel")) {
      if (notificationPanel) notificationPanel.classList.remove("open");
    }
  });

  document.getElementById("viewAllBtn")?.addEventListener("click", () => document.getElementById("history")?.scrollIntoView({ behavior: "smooth" }));

  document.querySelector(".table-footer")?.addEventListener("click", event => {
    const button = event.target.closest("button");
    if (!button || !latestScans.length) return;

    const pages = Math.max(1, Math.ceil(latestScans.length / 10));
    const label = button.textContent.trim();
    currentPage = label === "‹"
      ? Math.max(1, currentPage - 1)
      : label === "›"
        ? Math.min(pages, currentPage + 1)
        : Math.min(pages, Math.max(1, Number(label) || currentPage));

    renderHistory(latestScans);
  });

  document.querySelector("#scanTable tbody")?.addEventListener("click", event => {
    const button = event.target.closest("[data-scan-id]");
    if (!button) return;
    const scan = latestScans.find(item => item.id === Number(button.dataset.scanId));
    if (scan) {
      sessionStorage.setItem("secretScannerLastResult", JSON.stringify(scan));
      location.href = "results.html";
    }
  });

  document.getElementById("exportBtn")?.addEventListener("click", () => {
    const csv = ["Date,Type,Findings,Score"].concat(latestScans.map(scan => [scan.scanned_at, scan.input_type, scan.total_found, scan.score].join(","))).join("\n");
    const download = document.createElement("a");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    download.href = url;
    download.download = "secret-scanner-report.csv";
    download.click();
    URL.revokeObjectURL(url);
  });

  document.querySelectorAll(".recommend-grid button").forEach(button => {
    button.addEventListener("click", () => {
      const title = button.closest("article")?.querySelector("b")?.textContent || "Recommendation";
      alert(`${title}: review the recommendation and apply the change in your source repository.`);
    });
  });
});
