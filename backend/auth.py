"""
THIS IS ALL MY REQUIRED INSTRUCTIONS :-

auth.py
-------
Register / Login logic for Secret-Scanner_v1 (backend/auth.py)

Depends on:
  - models.py   -> db, User  (the "users" table)
  - app.py      -> creates the Flask app, calls db.init_app(app),
                   registers this blueprint, and configures JWTManager

Uses only what's already in backend/requirements.txt:
  - flask                -> Blueprint, request, jsonify
  - flask-sqlalchemy      -> via models.db
  - flask-jwt-extended    -> create_access_token (issues the JWT)
  - werkzeug (ships with Flask, no extra install needed)
                          -> generate_password_hash / check_password_hash
                             for encrypting passwords
"""

import random
import time
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

from models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
OTP_STORE = {}


def send_otp_email(email, otp):
    """Send OTP via email using SMTP. Falls back to local mode when SMTP is not configured."""
    smtp_server = os.environ.get("SMTP_SERVER", "").strip()
    smtp_port = os.environ.get("SMTP_PORT", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
    sender_email = os.environ.get("SENDER_EMAIL", smtp_user).strip()
    placeholder_values = {"your-email@gmail.com", "your-app-password", "changeme", "change-me"}

    demo_mode = os.environ.get("OTP_DEMO_MODE", "false").strip().lower() == "true"
    missing_smtp_config = not (smtp_server and smtp_port and smtp_user and smtp_password)
    placeholders_used = (
        smtp_user.lower() in placeholder_values
        or smtp_password.lower() in placeholder_values
        or sender_email.lower() in placeholder_values
    )

    if demo_mode or missing_smtp_config:
        return True, "Local mode: OTP will be displayed in browser"
    if placeholders_used:
        return False, "Email delivery is not configured"

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your Secret Scanner OTP"
        message["From"] = sender_email
        message["To"] = email

        text = f"Your one-time password (OTP) is: {otp}\n\nThis code will expire in 5 minutes."
        html = f"""\
        <html>
          <body>
            <h2>Secret Scanner - OTP Verification</h2>
            <p>Your one-time password is:</p>
            <h1 style="color: #22c55e; font-size: 32px; letter-spacing: 4px;">{otp}</h1>
            <p style="color: #666;">This code will expire in 5 minutes.</p>
            <p style="color: #999; font-size: 12px;">If you didn't request this, please ignore this email.</p>
          </body>
        </html>
        """

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)

        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, email, message.as_string())

        return True, "OTP sent to email"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"


def normalize_phone(phone):
    return (phone or "").replace(" ", "").replace("-", "").strip()


@auth_bp.route("/request-otp", methods=["POST"])
def request_otp():
    data = request.get_json(silent=True) or {}
    phone = normalize_phone(data.get("phone") if isinstance(data.get("phone"), str) else "")
    email_value = data.get("email")
    email = email_value.strip().lower() if isinstance(email_value, str) else ""

    if not phone and not email:
        return jsonify({"error": "phone or email is required"}), 400

    otp = str(random.randint(1000, 9999))
    identifier = email if email else phone
    OTP_STORE[identifier] = {"otp": otp, "expires_at": time.time() + 300}

    # Try to send email if email was provided
    if email:
        success, message = send_otp_email(email, otp)
        if not success:
            return jsonify({"error": message}), 500
        response = {"message": message}
        if message.lower().startswith(("demo", "local")):
            response["otp"] = otp
        return jsonify(response), 200

    # Phone-only mode (demo)
    return jsonify({"message": "OTP sent successfully", "otp": otp}), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    1. Receive -> name, email, phone, otp, password
    2. Verify -> OTP matches email or phone
    3. Check   -> email/phone already used?
    4. Encrypt -> hash the password
    5. Save    -> insert new user row
    6. Return  -> success + JWT token
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    email = data.get("email", "")
    phone = data.get("phone", "")
    otp = data.get("otp", "")
    password = data.get("password", "")

    if not all(isinstance(value, str) for value in (name, email, phone, otp, password)):
        return jsonify({"error": "All registration fields must be strings"}), 400
    name = name.strip()
    email = email.strip().lower()
    phone = normalize_phone(phone)
    otp = otp.strip()

    if not name or not email or not phone or not otp or not password:
        return jsonify({"error": "name, email, phone, otp and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400

    # Check OTP against email first (if email OTP was sent), then phone
    identifier = email if email in OTP_STORE else phone
    otp_record = OTP_STORE.get(identifier)
    if not otp_record or time.time() > otp_record["expires_at"] or otp_record["otp"] != otp:
        return jsonify({"error": "Invalid or expired OTP"}), 400

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({"error": "Email already exists"}), 409

    existing_phone = User.query.filter_by(phone=phone).first()
    if existing_phone:
        return jsonify({"error": "Phone number already exists"}), 409

    password_hash = generate_password_hash(password)
    new_user = User(name=name, email=email, phone=phone, password_hash=password_hash)
    db.session.add(new_user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already exists"}), 409
    finally:
        OTP_STORE.pop(identifier, None)

    token = create_access_token(identity=str(new_user.id))
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": new_user.to_dict()
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    1. Receive   -> email, password
    2. Find user -> by email
    3. Check     -> does password match the stored hash?
    4. Return    -> JWT token on success
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password must be strings"}), 400
    email = email.strip().lower()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    # ---- Step 2: find user by email ----
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    # ---- Step 3: check password matches ----
    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    # ---- Step 4: correct -> return JWT token ----
    token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict()
    }), 200
