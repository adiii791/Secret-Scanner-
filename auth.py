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

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

from models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    1. Receive -> name, email, password
    2. Check   -> is email already used?
    3. Encrypt -> hash the password
    4. Save    -> insert new user row
    5. Return  -> success + JWT token
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # ---- basic input validation ----
    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400

    # ---- Step 2: check if email already exists ----
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already exists"}), 409  # 409 Conflict

    # ---- Step 3: encrypt the password ----
    password_hash = generate_password_hash(password)

    # ---- Step 4: save user to database ----
    new_user = User(name=name, email=email, password_hash=password_hash)
    db.session.add(new_user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already exists"}), 409

    # ---- Step 5: return success + JWT token ----
    token = create_access_token(identity=str(new_user.id))
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": new_user.to_dict()
    }), 201  # 201 Created


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    1. Receive   -> email, password
    2. Find user -> by email
    3. Check     -> does password match the stored hash?
    4. Return    -> JWT token on success
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    # ---- Step 2: find user by email ----
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # ---- Step 3: check password matches ----
    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Wrong password"}), 401

    # ---- Step 4: correct -> return JWT token ----
    token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict()
    }), 200
