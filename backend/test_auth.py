import os
import unittest

os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-key-with-more-than-32-chars")

from app import app
from models import db


class AuthOtpFlowTest(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite://")
        with app.app_context():
            db.drop_all()
            db.create_all()
        self.client = app.test_client()

    def test_request_otp_returns_code(self):
        response = self.client.post(
            "/api/auth/request-otp",
            json={"phone": "+91 98765 43210"},
        )
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertIn("otp", data)
        self.assertTrue(len(data["otp"]) >= 4)

    def test_request_otp_email_falls_back_to_local_mode(self):
        response = self.client.post(
            "/api/auth/request-otp",
            json={"email": "local@example.com"},
        )
        data = response.get_json()
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertIn("otp", data)
        self.assertTrue(len(data["otp"]) >= 4)

    def test_register_requires_phone_and_valid_otp(self):
        otp_response = self.client.post(
            "/api/auth/request-otp",
            json={"phone": "+91 98765 43210"},
        )
        otp = otp_response.get_json()["otp"]

        response = self.client.post(
            "/api/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+91 98765 43210",
                "otp": otp,
                "password": "pass123",
            },
        )
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        self.assertIn("token", response.get_json())


if __name__ == "__main__":
    unittest.main()
