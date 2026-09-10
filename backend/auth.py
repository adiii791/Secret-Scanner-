"""Authentication blueprint — register, login, OTP request/verify."""

import random
import time
import smtplib
import os
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

from models import db, User, OtpRequest

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ---------------------------------------------------------------------------
# Email delivery helper
# ---------------------------------------------------------------------------

def send_otp_email(email, otp):
    """Send OTP via SMTP. Falls back to demo mode when SMTP is not configured."""
    smtp_server = os.environ.get("SMTP_SERVER", "").strip()
    smtp_port = os.environ.get("SMTP_PORT", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
    sender_email = os.environ.get("SENDER_EMAIL", smtp_user).strip()
    placeholder_values = {"your-email@gmail.com", "your-app-password", "changeme", "change-me"}

    demo_mode = os.environ.get("OTP_DEMO_MODE", "false").strip().lower() == "true"
    missing_smtp = not (smtp_server and smtp_port and smtp_user and smtp_password)
    has_placeholder = (
        smtp_user.lower() in placeholder_values
        or smtp_password.lower() in placeholder_values
        or sender_email.lower() in placeholder_values
    )

    if demo_mode or missing_smtp:
        return True, "Local mode: OTP will be displayed in browser"
    if has_placeholder:
        return False, "Email delivery is not configured"

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your Secret Scanner OTP"
        message["From"] = sender_email
        message["To"] = email

        text = f"Your one-time password (OTP) is: {otp}\n\nThis code expires in 5 minutes."
        html = f"""\
<html><body>
  <h2>Secret Scanner — OTP Verification</h2>
  <p>Your one-time password is:</p>
  <h1 style="color:#22c55e;font-size:32px;letter-spacing:4px;">{otp}</h1>
  <p style="color:#666;">This code expires in 5 minutes.</p>
  <p style="color:#999;font-size:12px;">If you didn't request this, ignore this email.</p>
</body></html>"""

        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, email, message.as_string())

        return True, "OTP sent to email"
    except Exception as exc:
        return False, f"Failed to send email: {exc}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_phone(phone):
    return (phone or "").replace(" ", "").replace("-", "").strip()


def _store_otp(identifier: str, otp: str) -> None:
    """Upsert an OTP record in the database (replaces any existing one)."""
    # Remove any previous pending OTP for this identifier.
    OtpRequest.query.filter_by(identifier=identifier).delete()
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    # Store a hash of the OTP so even a DB read doesn't expose it.
    otp_hash = generate_password_hash(otp)
    db.session.add(OtpRequest(identifier=identifier, otp_hash=otp_hash, expires_at=expires))
    db.session.commit()


def _verify_and_consume_otp(identifier: str, otp: str) -> bool:
    """Return True and delete the record if the OTP is valid and not expired."""
    record = OtpRequest.query.filter_by(identifier=identifier).first()
    if record is None:
        return False
    now = datetime.now(timezone.utc)
    # expires_at may be a naive datetime stored without tzinfo — normalise.
    expires = record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if now > expires or not check_password_hash(record.otp_hash, otp):
        return False
    db.session.delete(record)
    db.session.commit()
    return True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route("/request-otp", methods=["POST"])
def request_otp():
    data = request.get_json(silent=True) or {}
    phone_raw = data.get("phone") if isinstance(data.get("phone"), str) else ""
    phone = normalize_phone(phone_raw)
    email_raw = data.get("email")
    email = email_raw.strip().lower() if isinstance(email_raw, str) else ""

    if not phone and not email:
        return jsonify({"error": "phone or email is required"}), 400

    otp = str(random.randint(1000, 9999))
    # Prefer email as the identifier so the register endpoint can look it up
    # by email; fall back to phone for phone-only flows.
    identifier = email if email else phone
    _store_otp(identifier, otp)

    if email:
        success, message = send_otp_email(email, otp)
        if not success:
            return jsonify({"error": message}), 500
        response_body = {"message": message}
        # Return the OTP in the response only in local/demo mode.
        if message.lower().startswith(("demo", "local")):
            response_body["otp"] = otp
        return jsonify(response_body), 200

    # Phone-only path (demo mode only — no real SMS integration yet).
    return jsonify({"message": "OTP sent successfully", "otp": otp}), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    email = data.get("email", "")
    phone = data.get("phone", "")
    otp = data.get("otp", "")
    password = data.get("password", "")

    if not all(isinstance(v, str) for v in (name, email, phone, otp, password)):
        return jsonify({"error": "All registration fields must be strings"}), 400

    name = name.strip()
    email = email.strip().lower()
    phone = normalize_phone(phone)
    otp = otp.strip()

    if not name or not email or not phone or not otp or not password:
        return jsonify({"error": "name, email, phone, otp and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400

    # Verify OTP — try email identifier first, then phone.
    identifier = email if OtpRequest.query.filter_by(identifier=email).first() else phone
    if not _verify_and_consume_otp(identifier, otp):
        return jsonify({"error": "Invalid or expired OTP"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409
    if User.query.filter_by(phone=phone).first():
        return jsonify({"error": "Phone number already registered"}), 409

    new_user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash=generate_password_hash(password),
    )
    db.session.add(new_user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or phone already registered"}), 409

    token = create_access_token(identity=str(new_user.id))
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": new_user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password must be strings"}), 400
    email = email.strip().lower()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        # Same message for both cases — prevents user enumeration.
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict(),
    }), 200
