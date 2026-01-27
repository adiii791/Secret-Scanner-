
import logging
import re
from datetime import datetime
# this is a flask framework allow to use web application
from flask import Flask, jsonify, request

#this helps us to create flask application instance and name helps us to know where
# to look for resources
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

stats = {
    "total_scans": 0,
    "total_secrets_found": 0,
    "scans_by_severity": {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    },
    "scans_by_type": {},
    "started_at": datetime.now().isoformat(),
    "last_scan_at": None
}

def update_stats(scan_results):
# update global statistics with scan results
    stats["total_scans"] += 1
    stats["total_secrets_found"] += scan_results["total_issues"]
    stats["last_scan_at"] = datetime.now().isoformat()

    for finding in scan_results["findings"]:
        #updte severity counts
        severity = finding["severity"]
        stats["scans_by_severity"][severity] += 1

        #update type counts
        secret_type = finding["type"]
        if secret_type not in stats["scans_by_type"]:
            stats["scans_by_type"][secret_type] += 1

def scan_for_secrets(code):

# the pattern are defined by regex
    patterns = {
        "password": {
            "regex": r'password\s*[=:]\s*["\']([^"\']+)["\']',
            "severity": "CRITICAL",
            "description": "Hardcoded password detected",
            "recommendation": "use environment variables and secrets manager"
        },
        "api key": {
            "regex": r'api[_-]?key\s*[=:]\s*["\']([^"\']+)["\']',
            "severity": "CRITICAL",
            "description": "API key exposed in code",
            "recommendation": "store in environment variables"
        },
        "aws_access_key": {
            "regex": r'AKIA[0-9A-Z]{16}',
            "severity": "CRITICAL",
            "description": "AWS access key ID detected",
            "recommendation": "rotate keys immediately and use IAM roles"
        },
        "private key": {
            "regex": r'-----BEGIN.*PRIVATE KEY-----',
            "severity": "CRITICAL",
            "description": "private key found in code",
            "recommendation": "remove immediately and regenerate key"
        },
        "jwt_token": {
            "regex": r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
            "severity": "HIGH",
            "description": "JWT token detected",
            "recommendation": "never hardcode tokens in code"
        },
        "github_token": {
            "regex": r'ghp_[a-zA-Z0-9]{36}',
            "severity": "CRITICAL",
            "description": "github personal access token found",
            "recommendation": "revoke token immediately" 
        },
        "slack_token": {
            "regex": r'xox[baprs]-[0-9a-zA-Z]{10,48}',
            "severity": "HIGH",
            "description": "slack token detected",
            "recommendation": "rotate token immediately"
        }

    }

    findings = []
    lines = code.split('\n')

    for line_num, line in enumerate(lines, start=1):
        for secret_type, pattern_info in patterns.items():
            match = re.search(pattern_info["regex"], line, re.IGNORECASE)
            if match:
                findings.append({
                    "type": secret_type,
                    "severity": pattern_info["severity"],
                    "description": pattern_info["description"],
                    "recommendation": pattern_info["recommendation"],
                    "line_number": line_num,
                    "line_content": line.strip()[:100],
                    "found_at": datetime.now().isoformat()
                })

#calculate risk score
    risk_score = sum({
        "CRITICAL": 10,
        "HIGH": 7,
        "MEDIUM": 4,
        "LOW": 2
    }.get(f["severity"], 0) for f in findings)

    return{
    "findings": findings,
    "total_issues": len(findings),
    "risk_score": risk_score,
    "risk_level": "CRITICAL" if risk_score >= 20 else "HIGH" if risk_score >= 10 else "MEDIUM" if risk_score >= 5 else "LOW"
}

# this route is api document of the scanner for the user like guidlines how to use this api and json response
@app.route('/docs')
def docs():
    # in this feature comprehensive api documentation is provided
    return jsonify({
        "api": "Secret Scanner API",
        "version": "2.0",
        "description": "Advanced Security Scanning API for detecting hardcoded secrets in code.",
        "developer": "Adesh Gore",
        "base_url": "http://localhost:5001",

        "endpoints": {
            # This tells all info and mentioned endpoints in my code
            "GET /": {
                "description": "API information and status",
                "auth_required": False,
                "response": "API metadata" 

            },

            "POST /scan": {
                "description": "Scan code for security issues",
                "auth_required": False,
                "request_body": {
                    "code": "string (required) - Code to scan",
                    "options": {
                        "include_line_numbers": "boolean (optional) - ALL|CRITICAL|HIGH"
                    }
                },
                "response": "Detailed scan results with findings",
                "example": {
                    "code": "password = 'secret123'",
                    "options": {"severity_filter": "ALL"}
                }

            },

            "GET /health": {
                # health check point
                "description": "Health check endpoint",
                "auth_reuired": False,
                "response": "API health status"

            },

            "GET /stats": {
                # API statistics
                "description": "API usage statistics",
                "auth_required": False,
                "response": "Scan Statistics and Insights"
            },

            "GET /docs": {
                # API documentation
                "description": "this documentation",
                "auth_required": False,
                "response": "API documentation"
            }


        },

        "secret_types_deteced": [
            "password",
            "api key",
            "aws_access_key",
            "private_keys",
            "jwt_tokens",
            "github_tokens",
            "slack_tokens"
         
        ],

        "severity_levels": {
            "CRITICAL": "Immediate action required - severe security risk",
            "HIGH": "Fix soon - significant security risk",
            "MEDIUM": "Review recommended - moderate risk",
            "LOW": "Minor issue - low risk"

        }

    })
          
# @app.route() is a decorator and tells flask someone visits ('/') run this function
@app.route('/')
def home():
    #home endpoint with full API info.
    return jsonify({
        "api": "Secret Scanner API",
        "version": "2.0",
        "tagline": "Secure your code before it's too late",
        "status": "🟢 Online",

        "Stats": {
            "total_scans": stats["total_scans"],
            "secrets_prevented": stats["total_secrets_found"],
            "uptime": " Active since" + stats["started_at"]
        },

        "quick start": {
            "1": "POST your code to /scan endpoint",
            "2": "Receive detailed security analysis",
            "3": "Fix issues before commiting code",
            "example": "curl -X POST http://localhost:5001/scan -H 'Content-Type: application/json' -d '{\"code\":\"password=123\"}'"


        },

        "features": [
            "7 type of secrets detected",
            "Line_by_line analysis",
            "severity classification",
            "fix recommendations",
            "Usage statistics"
        ],

        "endpoints": {
            "documentation": "/docs",
            "scan": "/scan (POST)",
            "statistics": "/stats",
            "health": "/health",
            
        },

        "creator":{
            "name": "Adesh Gore",

        }

    })


# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": ["/", "/scan", "/health", "/stats", "/docs"]
    }), 404

# Error handler for 500
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred. Please try again."
    }), 500

# this accepts only POST requests and GET wont work here
@app.route('/scan', methods=['POST'])
def scan():
    try:
        logger.info(f"Scan request received from {request.remote_addr}")
        
        data = request.json
        if not data:
            return jsonify({
                "error": "Invalid JSON",
            }), 400
            
        code = data.get('code', '')

        if not code:
            # return erroe and give 400 status code
            return jsonify({
                "error": "No code provided",
            }), 400
        #perform scan
        scan_results = scan_for_secrets(code)

        #Apply severity filter if required
        severity_filter = data.get('severity_filter', 'ALL')
        if severity_filter != 'ALL':
            scan_results["findings"] = [
                f for f in scan_results["findings"]
                if f["severity"] == severity_filter
            ]
            scan_results["total_issues"] = len(scan_results["findings"])

        update_stats(scan_results)

        # Build response
        response = {
            "scan_id": f"scan_{stats['total_scans']}",
            "scanned_at": datetime.now().isoformat(),
            "results": scan_results,
            "summary": {
                "safe": scan_results["total_issues"] == 0,
                "issues_found": scan_results["total_issues"],
                "risk_level": scan_results["risk_level"],
                "message": _get_summary_message(scan_results)
            }
       }
        
        logger.info(f"Scan completed: {scan_results['total_issues']} issues found")
        return jsonify(response), 200
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500
    
def _get_summary_message(scan_results):
    # it generate readable summary message
    total = scan_results["total_issues"]
    risk = scan_results["risk_level"]

    if  total == 0:
        return "✅ Excellent! No security issues detected. Code is safe to proceed further."
    elif risk == "CRITICAL":
        return f"🔴 CRITICAL: found {total} critical security issue(s), Do not further proceed this code!"
    elif risk == "HIGH":
        return f"🟠 HIGH RISK: found {total} security issue(s). Fix before commiting."
    elif risk == "MEDIUM":
        return f"🟠 MEDIUM RISK: found {total} security issue(s). Review the code before commiting."
    else:
        return f"🟠 LOW RISK: found {total} potential issue(s). Consider fixing."


@app.route('/stats')
def get_stats():
    return jsonify({
        "statistics": stats,
        "insights": {
            "average_secrets_per_scan": round(
                stats["total_secrets_found"] / stats["total_scans"], 2
            ) if stats["total_scans"] > 0 else 0,
            "most_common_issue": max(
                stats["scans_by_type"].items(),
                key=lambda x: x[1]
            )[0] if stats["scans_by_type" ] else "None",
            "uptime": "Active"
        }
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "uptime": "running" 
    })

# this runs the application on local development server
# runs only if we call this file directly not if it imported as module
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Secret Scanner API Starting...")
    print("URL: http://localhost:5001")
    print("🔍 Ready to Scan for Secrets!")
    print("=" * 50)

    #debug=TRUE gives helpful error messages and never use this in production!
    import os
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 Starting Secret Scanner API v2.0")
    print(f"📍 Running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
