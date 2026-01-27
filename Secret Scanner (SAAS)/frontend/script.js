// ============================================
// SECRET SCANNER - DEMO MODE
// (Works without backend API)
// ============================================

const API_URL = 'https://adiii.pythonanywhere.com';
const DEMO_MODE = true; // Set to false when API is fixed

// ============================================
// LOAD EXAMPLE CODE
// ============================================
function loadExample() {
    const exampleCode = `# Example: Common security issues
password = "MySecret123"
api_key = "sk-1234567890abcdefghijklmnop"
aws_access_key = "AKIAIOSFODNN7EXAMPLE"
db_connection = "mongodb://admin:password@localhost:27017"
jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
private_key = "-----BEGIN RSA PRIVATE KEY-----"`;
    
    document.getElementById('code-input').value = exampleCode;
    
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = 'Loaded! ✓';
    btn.style.borderColor = '#10b981';
    
    setTimeout(() => {
        btn.textContent = originalText;
        btn.style.borderColor = '';
    }, 2000);
}

// ============================================
// SCAN CODE - CLIENT SIDE DETECTION
// ============================================
async function scanCode() {
    const code = document.getElementById('code-input').value.trim();
    
    if (!code) {
        alert('⚠️ Please paste some code first!');
        return;
    }
    
    const scanBtn = document.querySelector('.scan-button');
    const originalText = scanBtn.innerHTML;
    scanBtn.innerHTML = '⏳ Scanning...';
    scanBtn.disabled = true;
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    if (DEMO_MODE) {
        // Client-side secret detection
        const secrets = detectSecrets(code);
        displayResults({ secrets_found: secrets.length, details: secrets });
    } else {
        // Try real API
        try {
            const response = await fetch(`${API_URL}/scan`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ code: code })
            });
            const data = await response.json();
            displayResults(data);
        } catch (error) {
            // Fallback to demo mode
            const secrets = detectSecrets(code);
            displayResults({ secrets_found: secrets.length, details: secrets });
        }
    }
    
    scanBtn.innerHTML = originalText;
    scanBtn.disabled = false;
}

// ============================================
// CLIENT-SIDE SECRET DETECTION
// ============================================
function detectSecrets(code) {
    const secrets = [];
    const lines = code.split('\n');
    
    // Detection patterns
    const patterns = [
        {
            name: 'Password',
            regex: /(password|passwd|pwd)\s*=\s*["'][^"']+["']/gi,
            severity: 'CRITICAL',
            icon: '🔑'
        },
        {
            name: 'API Key',
            regex: /(api[_-]?key|apikey)\s*=\s*["'][^"']+["']/gi,
            severity: 'CRITICAL',
            icon: '🔑'
        },
        {
            name: 'AWS Key',
            regex: /AKIA[0-9A-Z]{16}/g,
            severity: 'CRITICAL',
            icon: '☁️'
        },
        {
            name: 'Secret Key',
            regex: /(secret[_-]?key|secretkey)\s*=\s*["'][^"']+["']/gi,
            severity: 'HIGH',
            icon: '🔐'
        },
        {
            name: 'Database URL',
            regex: /(mongodb|postgres|mysql):\/\/[^\s"']+/gi,
            severity: 'CRITICAL',
            icon: '💾'
        },
        {
            name: 'JWT Token',
            regex: /eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*/g,
            severity: 'HIGH',
            icon: '🎫'
        },
        {
            name: 'Private Key',
            regex: /-----BEGIN (RSA |EC )?PRIVATE KEY-----/g,
            severity: 'CRITICAL',
            icon: '🔒'
        },
        {
            name: 'Bearer Token',
            regex: /bearer\s+[a-zA-Z0-9\-._~+/]+=*/gi,
            severity: 'HIGH',
            icon: '🎫'
        }
    ];
    
    // Scan each line
    lines.forEach((line, lineIndex) => {
        patterns.forEach(pattern => {
            if (pattern.regex.test(line)) {
                secrets.push({
                    type: pattern.name,
                    line: lineIndex + 1,
                    severity: pattern.severity,
                    icon: pattern.icon,
                    recommendation: getRecommendation(pattern.name)
                });
            }
        });
    });
    
    return secrets;
}

function getRecommendation(type) {
    const recommendations = {
        'Password': 'Never hardcode passwords. Use environment variables or secret management services.',
        'API Key': 'Store API keys in .env file and add to .gitignore. Use environment variables.',
        'AWS Key': 'Rotate this key immediately! Use AWS IAM roles or AWS Secrets Manager.',
        'Secret Key': 'Move to environment variables. Never commit secrets to version control.',
        'Database URL': 'Use environment variables for database credentials. Add .env to .gitignore.',
        'JWT Token': 'JWT tokens should never be hardcoded. Store securely or regenerate.',
        'Private Key': 'CRITICAL: Private keys must never be in code. Use key management services.',
        'Bearer Token': 'Remove bearer tokens from code. Use secure token storage.'
    };
    return recommendations[type] || 'Move this secret to environment variables.';
}

// ============================================
// DISPLAY RESULTS
// ============================================
function displayResults(data) {
    const container = document.getElementById('results-container');
    
    const secrets = data.details || [];
    const secretsCount = data.secrets_found || secrets.length;
    
    const score = calculateScore(secretsCount);
    const grade = getGrade(score);
    
    let html = `
        <div class="security-score">
            <div class="score-number">${score}/100</div>
            <div class="score-grade">${grade}</div>
            <div style="margin-top: 1rem; color: var(--text-dim);">
                ${secretsCount} secret${secretsCount !== 1 ? 's' : ''} found
            </div>
        </div>
    `;
    
    if (secretsCount === 0) {
        html += `
            <div class="results-empty">
                <div class="empty-icon">✅</div>
                <p><strong>Excellent!</strong> No secrets detected.</p>
                <p style="color: var(--text-dim); font-size: 0.9rem; margin-top: 0.5rem;">
                    Your code appears secure. Keep it up!
                </p>
            </div>
        `;
    } else {
        secrets.forEach(secret => {
            html += `
                <div class="result-card ${secret.severity.toLowerCase()}">
                    <div class="result-header">
                        <span class="result-type">${secret.icon || '🔒'} ${secret.type}</span>
                        <span class="result-severity severity-${secret.severity.toLowerCase()}">${secret.severity}</span>
                    </div>
                    <div class="result-line">📍 Line ${secret.line}</div>
                    <div style="margin-top: 0.5rem; color: var(--text-dim); font-size: 0.9rem;">
                        💡 ${secret.recommendation}
                    </div>
                </div>
            `;
        });
        
        html += `
            <div style="margin-top: 1.5rem; padding: 1rem; background: var(--card-bg); border-radius: 8px; border-left: 3px solid var(--yellow);">
                <strong>⚠️ Action Required:</strong>
                <p style="color: var(--text-dim); margin-top: 0.5rem; font-size: 0.9rem;">
                    Remove these secrets and use environment variables instead.
                </p>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function calculateScore(count) {
    if (count === 0) return 100;
    if (count === 1) return 85;
    if (count === 2) return 70;
    if (count === 3) return 55;
    if (count <= 5) return 40;
    return Math.max(0, 25 - (count - 5) * 5);
}

function getGrade(score) {
    if (score >= 90) return 'A - Excellent';
    if (score >= 75) return 'B - Good';
    if (score >= 60) return 'C - Fair';
    if (score >= 50) return 'D - Poor';
    return 'F - Critical';
}

// ============================================
// OTHER FUNCTIONS
// ============================================

function copyCode() {
    const code = document.getElementById('api-example').textContent;
    navigator.clipboard.writeText(code).then(() => {
        const btn = event.target;
        btn.textContent = 'Copied! ✓';
        btn.style.color = '#10b981';
        setTimeout(() => {
            btn.textContent = 'Copy';
            btn.style.color = '';
        }, 2000);
    });
}

function notifyMe() {
    const email = prompt('📧 Enter your email for Premium updates:');
    if (email && email.includes('@')) {
        alert(`✅ Thanks! We'll notify you at ${email}`);
    }
}

async function updateStats() {
    // Mock stats for now
    document.getElementById('secrets-prevented').textContent = '1,247';
    document.getElementById('total-scans').textContent = '89';
}

function checkAPIStatus() {
    const statusEl = document.getElementById('api-status');
    if (statusEl) {
        statusEl.textContent = 'Demo Mode';
        statusEl.style.color = '#fbbf24';
    }
}

// Smooth scrolling
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    updateStats();
    checkAPIStatus();
});

function joinWaitlist(feature) {
    const email = prompt('📧 Enter email for early access:');
    if (email && email.includes('@')) {
        alert(`✅ You're on the waitlist for ${feature} integration!`);
        // TODO: Save to spreadsheet or database
        console.log(`Waitlist: ${email} for ${feature}`);
    }
}