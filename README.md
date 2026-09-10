# Secret Scanner

Flask API + static frontend for detecting exposed secrets (API keys, tokens, credentials) in source code using regex pattern matching.

## Architecture

```
secret-scanner/
├── backend/          # Flask API (app.py, auth.py, detector.py, webhook.py, models.py)
├── frontend/         # Static HTML/CSS/JS dashboard
├── wsgi.py           # Gunicorn / EB entry point
├── gunicorn.conf.py  # Production server config
├── Procfile          # PaaS process definition
├── Dockerfile        # Docker / ECS / App Runner image
└── .ebextensions/    # Elastic Beanstalk hooks
```

---

## Local Development

### Prerequisites
- Python 3.11+
- (Optional) Docker & Docker Compose

### Option A — Python virtualenv

```powershell
# 1. Create virtualenv and install dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Configure environment
cp .env.example backend/.env
# Edit backend/.env — set JWT_SECRET_KEY (min 32 chars) and AUTO_CREATE_DB=true

# 3. Start the dev server
cd backend
python app.py
```

App runs at **http://localhost:5000**

### Option B — Docker Compose (with PostgreSQL)

```bash
# Start app + postgres
docker-compose up --build

# Stop
docker-compose down
```

App runs at **http://localhost:5000**

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register` | — | Register a new user |
| `POST` | `/api/auth/login` | — | Login, returns JWT token |
| `POST` | `/api/scan` | Optional JWT | Scan code for secrets |
| `GET`  | `/api/history` | JWT | Get personal scan history |
| `GET`  | `/api/scans/<id>` | JWT | Get single scan detail |
| `GET`  | `/api/me` | JWT | Get current user |
| `PUT`  | `/api/me` | JWT | Update display name |
| `PUT`  | `/api/me/password` | JWT | Change password |
| `DELETE` | `/api/me` | JWT | Delete account |
| `GET`  | `/api/admin/database` | Admin JWT | Admin: view all users/scans |
| `POST` | `/api/webhook/github` | HMAC sig | GitHub push webhook |
| `GET`  | `/api/health` | — | Health check |

---

## AWS Deployment

Three paths are supported — choose based on your team's AWS experience:

| Path | Best for |
|------|----------|
| **Elastic Beanstalk** | Easiest, fully managed, recommended starting point |
| **ECS Fargate + ECR** | Production-grade containers, fine-grained control |
| **EC2 + RDS** | Maximum control, requires manual setup |

---

### Path 1 — AWS Elastic Beanstalk (recommended)

#### Prerequisites
- AWS account with admin or PowerUser permissions
- [EB CLI](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html): `pip install awsebcli`
- AWS RDS PostgreSQL instance (or Aurora Serverless v2)

#### Steps

```bash
# 1. Initialise the EB project (only needed once)
eb init secret-scanner --platform "Python 3.11 running on 64bit Amazon Linux 2023" --region us-east-1

# 2. Create the environment
eb create secret-scanner-prod \
  --instance-type t3.small \
  --elb-type application \
  --envvars "JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')"

# 3. Set remaining environment variables (never commit secrets)
eb setenv \
  DATABASE_URL="postgresql+psycopg://user:pass@your-rds-host:5432/secretscanner" \
  FLASK_DEBUG="false" \
  ADMIN_EMAIL="you@example.com" \
  CORS_ORIGINS="https://your-eb-url.elasticbeanstalk.com" \
  AUTO_CREATE_DB="false"

# 4. Run the first database migration (one-time)
eb ssh -c "cd /var/app/current && source /var/app/venv/*/bin/activate && cd backend && flask --app app db upgrade"

# 5. Deploy (repeat for every code change)
eb deploy

# 6. Open in browser
eb open
```

After first deploy, the `.ebextensions/01_python.config` hook runs `flask db upgrade` automatically on every subsequent deploy.

#### Setting up HTTPS (recommended)

1. Request a free certificate in [AWS ACM](https://console.aws.amazon.com/acm/) for your domain.
2. In EB Console → Environment → Configuration → Load Balancer → Add HTTPS listener (port 443) and select your cert.
3. Update `CORS_ORIGINS` to your `https://` URL.
4. Edit `.ebextensions/02_security.config` — replace the placeholder ARN with your real ACM certificate ARN.

---

### Path 2 — Docker on ECS Fargate

```bash
# 1. Build and push the image to ECR
AWS_ACCOUNT=123456789012
AWS_REGION=us-east-1
ECR_REPO=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/secret-scanner

aws ecr create-repository --repository-name secret-scanner --region $AWS_REGION

aws ecr get-login-password --region $AWS_REGION \
  | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t secret-scanner .
docker tag  secret-scanner:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

# 2. Create an ECS cluster, task definition, and service via the AWS Console
#    (or use the AWS CDK / Terraform — see below).
#    Point the task definition at the ECR image above.
#    Set all required environment variables as ECS task environment variables
#    or reference them from AWS Secrets Manager.
```

**Minimum required environment variables for the ECS task:**

| Variable | Value |
|----------|-------|
| `JWT_SECRET_KEY` | 32+ char random string (store in Secrets Manager) |
| `DATABASE_URL` | `postgresql+psycopg://user:pass@rds-host:5432/secretscanner` |
| `FLASK_DEBUG` | `false` |
| `CORS_ORIGINS` | Your CloudFront / ALB HTTPS origin |
| `ADMIN_EMAIL` | Admin email address |
| `AUTO_CREATE_DB` | `false` (run `flask db upgrade` as a migration task instead) |

---

### Path 3 — EC2 + RDS (manual)

```bash
# On the EC2 instance:

# 1. Install Python 3.11, git, pip
sudo dnf install -y python3.11 python3.11-pip git

# 2. Clone the repo
git clone https://github.com/YOUR_ORG/secret-scanner.git
cd secret-scanner

# 3. Install dependencies
pip3.11 install -r requirements.txt

# 4. Create /etc/secret-scanner.env (chmod 600, owned by app user)
#    Set all variables from .env.example

# 5. Run database migrations
cd backend
DATABASE_URL="..." flask --app app db upgrade

# 6. Run with gunicorn (systemd service recommended)
gunicorn --config ../gunicorn.conf.py wsgi:app
```

---

### Database Migrations

Always run migrations **before** starting the new application version:

```bash
# From the project root:
cd backend
flask --app app db upgrade

# To create a new migration after changing models.py:
flask --app app db migrate -m "describe the change"
flask --app app db upgrade
```

---

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | **Yes** | JWT signing key, min 32 chars |
| `DATABASE_URL` | **Yes** | PostgreSQL connection string |
| `FLASK_DEBUG` | No | `false` in production |
| `PORT` | No | Port gunicorn binds to (default `5000`) |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |
| `ADMIN_EMAIL` | No | Admin account email(s), comma-separated |
| `AUTO_CREATE_DB` | No | `true` only in dev; use migrations in prod |
| `GITHUB_WEBHOOK_SECRET` | No | GitHub webhook HMAC secret |
| `GITHUB_TOKEN` | No | PAT for scanning private repos |
| `SMTP_SERVER` | No | SMTP server for email alerts |
| `SMTP_PORT` | No | SMTP port (default `587`) |
| `SMTP_USER` | No | SMTP username |
| `SMTP_PASSWORD` | No | SMTP password |
| `SENDER_EMAIL` | No | From address for alert emails |

---

### Security Checklist for Production

- [ ] `JWT_SECRET_KEY` is at least 32 random characters and stored in Secrets Manager
- [ ] `FLASK_DEBUG=false`
- [ ] Database is in a **private subnet** — not publicly accessible
- [ ] HTTPS is enabled at the ALB / CloudFront layer
- [ ] `CORS_ORIGINS` lists only exact `https://` origins (no wildcards)
- [ ] `AUTO_CREATE_DB=false` — use Alembic migrations
- [ ] `.env` files, `*.db` files, and the ZIP archive are in `.gitignore` and never committed
- [ ] Regular RDS automated backups are enabled
- [ ] CloudWatch log groups are configured for gunicorn output
