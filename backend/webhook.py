import hmac
import hashlib
import requests
import os
import json
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from detector import scan_code

#it will keep webhook and app.py code separate and orgaized
webhook_bp = Blueprint("webhook", __name__)

# get info from .env file
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Function 1 - Verify Signature : it will make sure request is genuinel from the github webhook

def verify_signature(payload_body, signature_header):
    if not signature_header:
        return False

    # GitHub sends signature as "sha256=abc123..."
    try:
        hash_algorithm, github_signature = signature_header.split("=", 1)
    except ValueError:
        return False

    if hash_algorithm != "sha256":
        return False

    # Create our own signature using the secret
    expected_signature = hmac.new(  # hmac.new is a valid alias for hmac.HMAC
        GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Compare safely (prevents timing attacks)
    return hmac.compare_digest(expected_signature, github_signature)

# Function 2 - Fetch file from github

def fetch_file_content(repo_full_name, file_path, commit_sha):
    try:
        # GitHub API URL to get file content
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}?ref={commit_sha}"

        headers = {
            "Accept": "application/vnd.github.v3.raw"
        }

        # Add token if available (for private repos)
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return response.text
        else:
            return None

    except Exception as e:
        print(f"Error fetching file {file_path}: {str(e)}")
        return None

# Function 3 - It Will Extreact The Added And Modified Commits

def get_changed_files(commits):
    changed_files = []

    for commit in commits:
        # Get added files
        for file in commit.get("added", []):
            changed_files.append(file)

        # Get modified files
        for file in commit.get("modified", []):
            if file not in changed_files:
                changed_files.append(file)

    return changed_files

# Function 4 - It only scans code files : skip images,videos etc

def is_scannable(filename):
    # File extensions worth scanning
    scannable_extensions = [
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".env", ".json", ".yaml", ".yml",
        ".php", ".java", ".go", ".rb",
        ".sh", ".bash", ".txt", ".config",
        ".xml", ".html", ".css", ".sql"
    ]

    for ext in scannable_extensions:
        if filename.endswith(ext):
            return True

    return False

# Function 5 - SEND ALERT EMAIL
# Notifies developer if critical secrets found

def send_alert(pusher_email, repo_name, findings, score):
    # For now just print - can integrate SendGrid or SES later
    print(f"\n[ALERT] CRITICAL SECRET FOUND!")
    print(f"Repo     : {repo_name}")
    print(f"Pusher   : {pusher_email}")
    print(f"Score    : {score}/100")
    print(f"Findings : {len(findings)} secret(s) found")
    for finding in findings:
        if finding["severity"] == "Critical":
            print(f"  -> Line {finding['line']}: {finding['type']}")
    print("Alert would be sent to:", pusher_email)

#MAIN WEBHOOK ENDPOINT

@webhook_bp.route("/api/webhook/github", methods=["POST"])
def github_webhook():

    # -- Step 1: Verify signature --
    signature = request.headers.get("X-Hub-Signature-256")
    payload_body = request.get_data()

    if not GITHUB_WEBHOOK_SECRET:
        return jsonify({"error": "Webhook secret is not configured"}), 503
    if not verify_signature(payload_body, signature):
        return jsonify({
            "error": "Invalid signature - request not from GitHub"
        }), 403

    # -- Step 2: Parse the payload --
    try:
        payload = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON payload"}), 400

    if not isinstance(payload, dict):
        return jsonify({"error": "Empty payload"}), 400

    # -- Step 3: Extract key info --
    repo_name = payload.get("repository", {}).get("full_name", "unknown")
    pusher_email = payload.get("pusher", {}).get("email", "unknown")
    pusher_name = payload.get("pusher", {}).get("name", "unknown")
    commits = payload.get("commits", [])
    ref = payload.get("ref", "")

    if not isinstance(commits, list) or any(not isinstance(commit, dict) for commit in commits):
        return jsonify({"error": "Invalid commits payload"}), 400

    print(f"\n[WEBHOOK] Push received from {pusher_name} on {repo_name}")
    print(f"Branch: {ref}")

    # -- Step 4: Get changed files --
    changed_files = get_changed_files(commits)

    if not changed_files:
        return jsonify({
            "message": "No files changed",
            "scanned": 0
        }), 200

    # Filter only scannable files
    scannable_files = [f for f in changed_files if isinstance(f, str) and is_scannable(f)][:100]

    if not scannable_files:
        return jsonify({
            "message": "No scannable files in this push",
            "scanned": 0
        }), 200

    print(f"Files to scan: {scannable_files}")

    # -- Step 5: Scan each file --
    all_findings = []
    scanned_files = []
    latest_commit_sha = commits[-1].get("id", "HEAD") if commits else "HEAD"

    for file_path in scannable_files:
        # Fetch file content from GitHub
        content = fetch_file_content(repo_name, file_path, latest_commit_sha)

        if content:
            # Scan the file
            result = scan_code(content)

            if result["total_found"] > 0:
                # Add file name to each finding
                for finding in result["findings"]:
                    finding["file"] = file_path
                    all_findings.append(finding)

            scanned_files.append({
                "file": file_path,
                "score": result["score"],
                "findings": result["total_found"]
            })

            print(f"  [OK] {file_path} - Score: {result['score']}/100 - Found: {result['total_found']}")

    # -- Step 6: Calculate overall score --
    if scanned_files:
        overall_score = sum(f["score"] for f in scanned_files) // len(scanned_files)
    else:
        overall_score = 100

    # -- Step 7: Send alert if critical found --
    critical_findings = [f for f in all_findings if f["severity"] == "Critical"]

    if critical_findings:
        send_alert(pusher_email, repo_name, all_findings, overall_score)

    # Webhook scans are deliberately not persisted: Scan.user_id is required so
    # each saved result is visible only in its authenticated owner's history.

    # -- Step 9: Return summary --
    return jsonify({
        "success": True,
        "repo": repo_name,
        "pusher": pusher_name,
        "files_scanned": len(scanned_files),
        "total_secrets_found": len(all_findings),
        "overall_score": overall_score,
        "critical_found": len(critical_findings),
        "results": scanned_files
    }), 200




