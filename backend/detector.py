import re


PATTERNS = [
    {
        "name" : "AWS Access Key",
        "regex" : r"AKIA[0-9A-Z]{16}",
        "severity" : "Critical",
        "fix" : "Revoke or Remove it from your source code and store it on .env file"
    },

    {
        "name" : "JWT Token",
        "regex" : r'(?<![A-Za-z0-9_-])[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+(?![A-Za-z0-9_-])',
        "severity" : "High",
        "fix" : "Remove the exposed JWT immediately, revoke and rotate the token, and store secrets securely using environment variables"

    },

    {
        "name" : "SSH Private Key",
        "regex" : r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "severity" : "High",
        "fix" : "Immediately remove the exposed SSH private key, revoke or replace it with a new key pair, update the authorized keys on affected systems, and store private keys securely using a secrets manager"

    },

    {
        "name" : "Google API Key",
        "regex" : r"AIza[0-9A-Za-z\-_]{35}",
        "severity" : "Critical",
        "fix" : "Remove the exposed Google API key immediately, rotate or regenerate the key, restrict it by application, IP address, HTTP referrer, or API usage as appropriate, and store it securely using environment variables"
    },

    {
        "name" : "AWS Secret Key",
        "regex" : r"(?i)aws(.{0,20})?['\"][0-9a-zA-Z\/+]{40}['\"]",
        "severity" : "Critical",
        "fix" : "Immediately remove the exposed AWS Secret Access Key, deactivate or rotate the compromised credentials, create a new access key with the principle of least privilege, and store AWS credentials securely using AWS Secrets Manager"
    },

    {
        "name" : "Slack User Token",
        "regex" : r"xoxp-[0-9]{11}-[0-9]{11}-[0-9]{11}-[a-zA-Z0-9]{32}",
        "severity" : "High",
        "fix" : "Immediately revoke the exposed Slack user token, generate a new token with the minimum required scopes, review logs for unauthorized access, and store the token securely using environment variables"
    },

    {
        "name" : "Slack Bot Token",
        "regex" : r"xoxb-[0-9]{11}-[0-9]{11}-[a-zA-Z0-9]{24}",
        "severity" : "High",
        "fix" : "Immediately revoke the exposed Slack bot token, generate a new token with only the required OAuth scopes, review the bot's activity for unauthorized access, and store the token securely using environment variablesre the token securely using environment variables"
    },

    {
        "name" : "Slack Webhook URL",
        "regex" : r"https:\/\/hooks\.slack\.com\/services\/T[a-zA-Z0-9]+\/B[a-zA-Z0-9]+\/[a-zA-Z0-9]+",
        "severity" : "High",
        "fix" : "Immediately revoke the exposed Slack Incoming Webhook URL, generate a new webhook, restrict its usage to the required workspace and channels, and store it securely using environment variables"
    },

    {
        "name" : "Database URL with credentials",
        "regex" : r"(mysql|postgresql|mongodb|sqlite|redis):\/\/[^:]+:[^@]+@[^\s]+",
        "severity" : "Critical",
        "fix" : "Immediately remove the exposed database URL containing credentials, rotate the compromised username and password, restrict database access using network controls and the principle of least privilege, and store connection strings securely using environment variables"
    },

    {
        "name" : "MongoDB Connection String",
        "regex" : r"mongodb\+srv:\/\/[^:]+:[^@]+@[^\s]+",
        "severity" : "Critical",
        "fix" : "Immediately remove the exposed MongoDB connection string, rotate the compromised database credentials, restrict database access using IP allowlists and the principle of least privilege, and store connection strings securely using environment variables"
    },

    {
        "name" : "Firebase API key",
        "regex" : r"AAAA[A-Za-z0-9_-]{7}:[A-Za-z0-9_-]{140}",
        "severity" : "Critical",
        "fix" : "Immediately remove the exposed Firebase API key, rotate or regenerate the key, restrict it by application, IP address, HTTP referrer, or API usage as appropriate, and store it securely using environment variables"
    }
]

def calculate_score(findings):
    score = 100

    deductions = {
        "Critical" : 35,
        "High" : 25,
        "Medium" : 15,
        "Low" : 5
    }

    for finding in findings:
        severity = finding["severity"]
        score = score - deductions[severity]

    if score < 0:
        score = 0

    return score

def scan_code(code):
    findings = []

    lines = code.split("\n")

    for line_number, line in enumerate(lines, start=1):

        for pattern in PATTERNS:
            match = re.search(pattern["regex"], line)

            if match:
                matched_value = match.group()

                if len(matched_value) > 6:
                    preview = matched_value[:6] + "***"

                else :
                    preview = "***"

                findings.append({
                    "line": line_number,
                    "type": pattern["name"],
                    "preview": preview,
                    "severity": pattern["severity"],
                    "fix": pattern["fix"]
                })

    score = calculate_score(findings)

    return{
        "score": score,
        "total_found": len(findings),
        "findings": findings
    }


