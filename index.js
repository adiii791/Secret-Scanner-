// Splash
window.addEventListener('load', () => {
    const splash = document.getElementById('splash');
    const mainContent = document.getElementById('main-content');

    setTimeout(() => {
        splash.classList.add('hide');
        setTimeout(() => {
            splash.style.display = 'none';
            mainContent.classList.remove('hidden');
            mainContent.classList.add('show');
        }, 800);
    }, 2500);
});

// Tabs
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
    });
});

// Scan button
document.getElementById("scanBtn").onclick = function () {
    window.location.href = "results.html";
};

// Dark / Light Mode (WORKING)
const html = document.documentElement;
const darkBtn = document.getElementById("darkBtn");
const lightBtn = document.getElementById("lightBtn");

if (darkBtn && lightBtn) {
    darkBtn.onclick = function () {
        html.setAttribute("data-theme", "dark");
        darkBtn.classList.add("active");
        lightBtn.classList.remove("active");
    };

    lightBtn.onclick = function () {
        html.setAttribute("data-theme", "light");
        lightBtn.classList.add("active");
        darkBtn.classList.remove("active");
    };
}