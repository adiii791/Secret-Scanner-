# Secret Scanner

Flask API and static dashboard for detecting exposed secrets in source code.

## Local setup

1. Create a virtual environment and install dependencies:

	```powershell
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	pip install -r requirements.txt
	```

2. Copy `backend/.env.example` to `backend/.env` and provide a strong
	`JWT_SECRET_KEY`. Keep `OTP_DEMO_MODE=true` only for local testing.

3. For a new local database, set `AUTO_CREATE_DB=true`, then start the
	development server from `backend/`:

	```powershell
	python app.py
	```

## AWS deployment

Use AWS Secrets Manager or Parameter Store for `JWT_SECRET_KEY`,
`DATABASE_URL`, SMTP credentials, and webhook credentials. Do not upload a
`.env` file, the ZIP archive, or database files.

Configure these environment variables in the service:

- `JWT_SECRET_KEY`: random value with at least 32 characters
- `DATABASE_URL`: production PostgreSQL connection string
- `FLASK_DEBUG=false`
- `CORS_ORIGINS`: exact HTTPS frontend origin(s), comma-separated
- `ADMIN_EMAIL`: comma-separated administrator email addresses
- `OTP_DEMO_MODE=false`

Before the first production start, run `flask --app app db upgrade` from
`backend/` against the production `DATABASE_URL`. Then run the application
with the production WSGI server:

```text
gunicorn --chdir backend --bind 0.0.0.0:$PORT --workers 2 --timeout 60 app:app
```

Use HTTPS at the AWS load balancer or CloudFront, restrict database network
access to the application, and configure backups.
