"""Secret Scanner HTTP API and frontend host."""
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from functools import wraps

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required, verify_jwt_in_request
try:
    from flask_migrate import Migrate
except ImportError:
    Migrate = None

from detector import scan_code
from models import Scan, User, ScanRateEntry, db
from auth import auth_bp
from webhook import webhook_bp

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
secret_key = os.environ.get("JWT_SECRET_KEY", "").strip()
if len(secret_key) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be configured with at least 32 characters")

admin_emails = {
    email.strip().lower()
    for email in os.environ.get("ADMIN_EMAIL", "").replace("\n", ",").split(",")
    if email.strip()
}
app.config.update(
    JWT_SECRET_KEY=secret_key,
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=24),
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///secretscanner.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    ADMIN_EMAILS=admin_emails,
    MAX_CONTENT_LENGTH=1 * 1024 * 1024,
    AUTO_CREATE_DB=os.environ.get("AUTO_CREATE_DB", "false").lower() == "true",
)
allowed_origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "http://127.0.0.1:5001,http://localhost:5001").split(",") if origin.strip()]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
JWTManager(app)
db.init_app(app)
if Migrate is not None:
    Migrate(app, db)
app.register_blueprint(auth_bp)
app.register_blueprint(webhook_bp)

if app.config["AUTO_CREATE_DB"]:
    with app.app_context():
        db.create_all()

@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' https://fonts.googleapis.com https://cdnjs.cloudflare.com 'unsafe-inline'; font-src https://fonts.gstatic.com https://cdnjs.cloudflare.com; connect-src 'self'")
    return response


def allow_scan_request():
    """DB-backed sliding-window rate limiter — works across all gunicorn workers."""
    client_key = (
        request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        .split(",")[0].strip()[:64]
    )
    window_start = datetime.now(timezone.utc) - timedelta(seconds=60)
    # Count hits in the last 60 seconds for this client.
    recent_count = ScanRateEntry.query.filter(
        ScanRateEntry.client_key == client_key,
        ScanRateEntry.hit_at >= window_start,
    ).count()
    if recent_count >= 30:
        return False
    # Record this hit.
    db.session.add(ScanRateEntry(client_key=client_key))
    # Purge old entries for this client (keeps the table small).
    ScanRateEntry.query.filter(
        ScanRateEntry.client_key == client_key,
        ScanRateEntry.hit_at < window_start,
    ).delete()
    db.session.commit()
    return True


def admin_required(view):
    """Restrict database administration to the account in ADMIN_EMAIL."""
    @wraps(view)
    @jwt_required()
    def wrapped(*args, **kwargs):
        user = db.session.get(User, int(get_jwt_identity()))
        if user is None or user.email.lower() not in app.config["ADMIN_EMAILS"]:
            return jsonify({"error": "Administrator access required"}), 403
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def frontend():
    return app.send_static_file("Login.html")


@app.route("/api/scan", methods=["POST"])
def scan():
    if not allow_scan_request():
        return jsonify({"error": "Too many scan requests. Try again later."}), 429
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    if not isinstance(code, str) or not code.strip():
        return jsonify({"error": "A non-empty code value is required"}), 400
    input_type = data.get("input_type", "paste")
    if input_type not in {"paste", "file", "github"}:
        return jsonify({"error": "input_type must be paste, file, or github"}), 400

    result = scan_code(code)
    # Guests may scan, but only authenticated users receive persistent history.
    verify_jwt_in_request(optional=True)
    user_id = get_jwt_identity()
    if user_id:
        new_scan = Scan(
            user_id=int(user_id),
            input_type=input_type,
            code_snippet=None,
            score=result["score"],
            total_found=result["total_found"],
            findings=result["findings"],
        )
        db.session.add(new_scan)
        db.session.commit()
        result["scan_id"] = new_scan.id

    return jsonify({"success": True, **result}), 200


@app.route("/api/history", methods=["GET"])
@jwt_required()
def history():
    scans = Scan.query.filter_by(user_id=int(get_jwt_identity())).order_by(Scan.scanned_at.desc()).all()
    return jsonify({"success": True, "total_scans": len(scans), "scans": [scan.to_dict() for scan in scans]})


@app.route("/api/scans/<int:scan_id>", methods=["GET"])
@jwt_required()
def scan_detail(scan_id):
    scan = Scan.query.filter_by(id=scan_id, user_id=int(get_jwt_identity())).first()
    if scan is None:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify({"scan": scan.to_dict()})


@app.route("/api/me", methods=["GET"])
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict(), "is_admin": user.email.lower() in app.config["ADMIN_EMAILS"]})


@app.route("/api/me", methods=["PUT"])
@jwt_required()
def update_me():
    user = db.session.get(User, int(get_jwt_identity()))
    name = ((request.get_json(silent=True) or {}).get("name") or "").strip()
    if user is None:
        return jsonify({"error": "User not found"}), 404
    if not name:
        return jsonify({"error": "Name is required"}), 400
    user.name = name
    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()})


@app.route("/api/me/password", methods=["PUT"])
@jwt_required()
def update_password():
    from werkzeug.security import check_password_hash, generate_password_hash
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None or not check_password_hash(user.password_hash, current_password):
        return jsonify({"error": "Current password is incorrect"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"message": "Password updated"})


@app.route("/api/me", methods=["DELETE"])
@jwt_required()
def delete_me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return jsonify({"error": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Account deleted"})


@app.route("/api/admin/database", methods=["GET"])
@admin_required
def admin_database():
    users = User.query.order_by(User.created_at.desc()).all()
    scans = Scan.query.order_by(Scan.scanned_at.desc()).limit(200).all()
    return jsonify({
        "summary": {"users": len(users), "scans": Scan.query.count()},
        "users": [user.to_dict() for user in users],
        "scans": [{**scan.to_dict(), "user_email": scan.user.email} for scan in scans],
    })


@app.route("/api/health", methods=["GET"])
def health():
    database_url = app.config["SQLALCHEMY_DATABASE_URI"]
    try:
        db.session.execute(db.text("SELECT 1"))
        database_status = "connected"
    except Exception:
        database_status = "unavailable"
    status_code = 200 if database_status == "connected" else 503
    return jsonify({
        "status": "running",
        "message": "SecretScanner API is live",
        "version": "2.0",
        "database": database_status,
        "database_backend": "postgresql" if database_url.startswith("postgresql") else "sqlite",
        "admin_configured": bool(app.config["ADMIN_EMAILS"]),
    }), status_code


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true", port=int(os.environ.get("PORT", 5000)))
