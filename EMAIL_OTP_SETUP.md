# Email OTP Setup Guide

## Current Status
The Secret Scanner app now supports **email-based OTP verification** for user registration. 

### Demo Mode (Current)
- OTP is **generated and displayed in the browser** during signup
- Useful for local development and testing
- No external email service needed

### Production Mode (with email delivery)
- OTP is **sent via email** and not displayed in browser
- Requires SMTP credentials to be configured
- More secure for production deployments

---

## How to Enable Email OTP Delivery

### Option 1: Gmail (Recommended for Testing)

1. **Enable 2-Step Verification** on your Gmail account:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Create an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the generated 16-character password

3. **Update `.env` file** in `backend/`:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SENDER_EMAIL=your-email@gmail.com
   ```

4. **Restart the Flask app**:
   ```bash
   python app.py
   ```

### Option 2: Other Email Providers

**Outlook/Hotmail:**
```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
SENDER_EMAIL=your-email@outlook.com
```

**SendGrid:**
```env
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SENDER_EMAIL=your-verified-sender@example.com
```

---

## Testing the Flow

### Demo Mode
1. Go to http://127.0.0.1:5001/
2. Click "Create account"
3. Fill in Name, Email, and Phone
4. Click "Send OTP"
5. OTP will appear in the green success message
6. Enter the OTP and complete signup

### With Email Delivery
1. After configuring SMTP credentials above
2. The OTP will be **sent to the email address** instead
3. User checks their inbox for the OTP code
4. Enter OTP to complete signup

---

## Code Changes Made

### Backend (`backend/auth.py`)
- Added `send_otp_email()` function for SMTP email delivery
- Updated `/api/auth/request-otp` to send emails when configured
- Updated `/api/auth/register` to accept email-based OTP identifiers
- Added environment variable support for SMTP configuration
- Falls back to demo mode if SMTP not configured

### Frontend (`frontend/js/Login.js`)
- Updated `sendOtp()` function to send email parameter
- Conditional message display based on mode (demo vs email)
- Validates both email and phone before sending OTP

### Configuration (`backend/.env`)
- Added SMTP configuration variables
- Included examples for Gmail, Outlook, and SendGrid

---

## Security Notes

1. **Never commit credentials** - Use environment variables only
2. **App-specific passwords** - Use generated app passwords, not your actual password
3. **5-minute expiry** - OTPs expire after 5 minutes for security
4. **Demo mode display** - Only shows OTP in development/testing

---

## API Endpoints

### Request OTP
**POST** `/api/auth/request-otp`
```json
{
  "email": "user@example.com",
  "phone": "+1 (555) 123-4567"
}
```

**Response (Demo Mode):**
```json
{
  "message": "Demo mode: OTP will be displayed in browser",
  "otp": "1234"
}
```

**Response (Email Mode):**
```json
{
  "message": "OTP sent to email",
  "otp": "1234"
}
```

### Register User
**POST** `/api/auth/register`
```json
{
  "name": "John Doe",
  "email": "user@example.com",
  "phone": "+1 (555) 123-4567",
  "otp": "1234",
  "password": "SecurePassword123"
}
```

---

## Testing Email Configuration

If SMTP is misconfigured, you'll get an error like:
```
{"error": "Failed to send email: [SMTP error details]"}
```

To debug:
1. Check credentials in `.env`
2. Verify SMTP server address and port are correct
3. Check if 2FA/App passwords are enabled (for Gmail)
4. Test SMTP connection using Python:
   ```python
   import smtplib
   server = smtplib.SMTP("smtp.gmail.com", 587)
   server.starttls()
   server.login("email@gmail.com", "app-password")
   ```
