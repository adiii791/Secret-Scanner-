# Secret Scanner

Flask API + static frontend for detecting exposed secrets (API keys, tokens, credentials) in source code.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Git

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/adiii791/Secret-Scanner-
cd Secret-Scanner-

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Mac / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your environment file
cp backend/.env.example backend/.env
# No edits needed — the defaults use SQLite and work out of the box

# 5. Run the app
cd backend
python app.py
```

Open your browser at **http://localhost:5000**

> **Note:** The `.env` file is gitignored and will never be committed. Each teammate must create their own from `.env.example`.

---

## 🐳 Docker Compose (Alternative — no Python install needed)

```bash
# From project root:
docker-compose up --build
```

App runs at **http://localhost:5000**

---

## 📁 Project Structure

```
Secret-Scanner/
├── backend/              # Flask API
│   ├── app.py            # Main application entry point ← run this
│   ├── auth.py           # Register / login / OTP routes
│   ├── detector.py       # Secret scanning engine
│   ├── models.py         # SQLAlchemy models
│   ├── webhook.py        # GitHub webhook handler
│   ├── .env.example      # Copy to backend/.env for local dev
│   └── migrations/       # Alembic DB migrations
├── frontend/             # Static HTML/CSS/JS
│   ├── Login.html        # Login / Register page
│   ├── index.html        # Scanner dashboard
│   ├── results.html      # Scan results
│   ├── profile.html      # User profile
│   └── css/ js/          # Stylesheets and scripts
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker image
├── docker-compose.yml    # Docker Compose (app + postgres)
├── gunicorn.conf.py      # Production WSGI config
├── Procfile              # PaaS process definition
└── .ebextensions/        # AWS Elastic Beanstalk hooks
```

---

## 🔑 Environment Variables

| Variable | Dev Default | Description |
|----------|-------------|-------------|
| `JWT_SECRET_KEY` | set in `.env` | JWT signing key (min 32 chars) |
| `DATABASE_URL` | `sqlite:///secretscanner.db` | DB connection string |
| `FLASK_DEBUG` | `true` | Enable debug mode |
| `AUTO_CREATE_DB` | `true` | Auto-create DB tables on startup (dev only) |
| `PORT` | `5000` | Port to listen on |
| `CORS_ORIGINS` | `http://localhost:5000` | Allowed origins |
| `ADMIN_EMAIL` | *(blank)* | Email(s) with admin access |
| `OTP_DEMO_MODE` | `true` | Skip real OTP delivery in dev |

---

## 🌐 API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register` | — | Register a new user |
| `POST` | `/api/auth/login` | — | Login, returns JWT token |
| `POST` | `/api/scan` | Optional JWT | Scan code for secrets |
| `GET`  | `/api/history` | JWT | Personal scan history |
| `GET`  | `/api/scans/<id>` | JWT | Single scan detail |
| `GET`  | `/api/me` | JWT | Current user profile |
| `PUT`  | `/api/me` | JWT | Update display name |
| `PUT`  | `/api/me/password` | JWT | Change password |
| `DELETE` | `/api/me` | JWT | Delete account |
| `GET`  | `/api/admin/database` | Admin JWT | View all users/scans |
| `POST` | `/api/webhook/github` | HMAC sig | GitHub push webhook |
| `GET`  | `/api/health` | — | Health check |

---

## ☁️ AWS Deployment

### Option A — Elastic Beanstalk (recommended)

```bash
# Install EB CLI
pip install awsebcli

# Deploy
eb init secret-scanner --platform "Python 3.11 running on 64bit Amazon Linux 2023" --region us-east-1
eb create secret-scanner-prod --instance-type t3.small --elb-type application

# Set production environment variables (never commit these)
eb setenv \
  JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  DATABASE_URL="postgresql+psycopg://user:pass@your-rds-host:5432/secretscanner" \
  FLASK_DEBUG="false" \
  AUTO_CREATE_DB="false" \
  ADMIN_EMAIL="you@example.com" \
  CORS_ORIGINS="https://your-eb-url.elasticbeanstalk.com"

# Run DB migrations (first deploy only)
eb ssh -c "cd /var/app/current/backend && flask --app app db upgrade"

eb deploy
eb open
```

### Option B — Docker on ECS / EC2

```bash
docker build -t secret-scanner .
docker run -p 5000:5000 \
  -e JWT_SECRET_KEY="your-secret-key" \
  -e DATABASE_URL="postgresql+psycopg://..." \
  -e FLASK_DEBUG="false" \
  -e AUTO_CREATE_DB="false" \
  secret-scanner
```

---

## 🛡️ Production Security Checklist

- [ ] `JWT_SECRET_KEY` is at least 32 random characters
- [ ] `FLASK_DEBUG=false`
- [ ] `AUTO_CREATE_DB=false` — use `flask db upgrade` instead
- [ ] Database is in a private subnet
- [ ] HTTPS is enabled
- [ ] `CORS_ORIGINS` lists only exact `https://` origins
- [ ] `.env` files are never committed
