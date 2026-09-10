"""
THIS IS ALL MY REQUIRED INSTRUCTIONS AGAIN :-

models.py
---------
Database schema for Secret-Scanner_v1 (backend/models.py)

Think of this file as designing 2 Excel sheets inside PostgreSQL:

  Sheet 1 -> "users"  -> everyone who registers on the platform
  Sheet 2 -> "scans"  -> every scan a user runs, linked back to that user

The `db` object is created ONCE here and shared with every other file
(app.py, auth.py, webhook.py, etc.) through `db.init_app(app)`.
This avoids the classic Flask bug of "two different SQLAlchemy instances
that don't know about each other."
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

# Single shared SQLAlchemy instance -> imported by app.py, auth.py, webhook.py
db = SQLAlchemy()


class User(db.Model):
    """
    Table: users
    One row = one registered person.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)                 # auto number
    name = db.Column(db.String(120), nullable=False)              # text
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)  # unique text
    phone = db.Column(db.String(30), unique=True, nullable=True, index=True)  # phone for OTP verification
    password_hash = db.Column(db.String(255), nullable=False)     # encrypted text (never store raw password)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # One user -> many scans. `cascade` means: if a user is deleted,
    # their scan history is deleted with them (keeps the DB clean).
    scans = db.relationship(
        "Scan",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Safe representation for API responses (never includes password_hash)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


class Scan(db.Model):
    """
    Table: scans
    One row = one scan a user ran (paste / file upload / GitHub repo).
    """
    __tablename__ = "scans"

    id = db.Column(db.Integer, primary_key=True)                                  # auto number
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)  # connects to User table

    input_type = db.Column(db.String(20), nullable=False)   # 'paste' | 'file' | 'github'
    code_snippet = db.Column(db.String(500))                # first 500 chars of scanned code
    score = db.Column(db.Integer, nullable=False, default=0)       # 0-100 risk/health score
    total_found = db.Column(db.Integer, nullable=False, default=0) # how many secrets detected
    findings = db.Column(db.JSON, nullable=False, default=list)      # full scan results as JSON
    scanned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.CheckConstraint("input_type IN ('paste','file','github')", name="ck_scan_input_type"),
        db.CheckConstraint("score >= 0 AND score <= 100", name="ck_scan_score_range"),
        db.CheckConstraint("total_found >= 0", name="ck_scan_total_found_nonneg"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "input_type": self.input_type,
            "code_snippet": self.code_snippet,
            "score": self.score,
            "total_found": self.total_found,
            "findings": self.findings,
            "scanned_at": self.scanned_at.isoformat() if self.scanned_at else None,
        }

    def __repr__(self):
        return f"<Scan id={self.id} user_id={self.user_id} score={self.score}>"


class OtpRequest(db.Model):
    """
    Table: otp_requests
    One row = one pending OTP verification (email or phone).
    Stored in the database so all gunicorn workers can share it.
    Rows are deleted immediately after successful use or expiry.
    """
    __tablename__ = "otp_requests"

    id = db.Column(db.Integer, primary_key=True)
    # The identifier is either a normalised email or a normalised phone number.
    identifier = db.Column(db.String(255), nullable=False, index=True)
    otp_hash = db.Column(db.String(255), nullable=False)   # bcrypt/pbkdf2 hash of the 4-digit code
    expires_at = db.Column(db.DateTime, nullable=False)    # UTC expiry timestamp

    def __repr__(self):
        return f"<OtpRequest id={self.id} identifier={self.identifier}>"


class ScanRateEntry(db.Model):
    """
    Table: scan_rate_entries
    Lightweight per-IP sliding-window counter for the /api/scan rate limiter.
    Works across all gunicorn workers since it uses the shared database.
    Rows older than 60 seconds are ignored and periodically purged.
    """
    __tablename__ = "scan_rate_entries"

    id = db.Column(db.Integer, primary_key=True)
    client_key = db.Column(db.String(64), nullable=False, index=True)
    hit_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ScanRateEntry id={self.id} client={self.client_key}>"
