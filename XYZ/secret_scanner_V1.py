# this is a flask framework allow to use web application
from flask import Flask, jsonify, request

#this helps us to create flask application instance and name helps us to know where
# to look for resources
app = Flask(__name__)

stats = {
    "total_scans": 0,
    "total_secrets_found": 0
}

def scan_for_secrets(code):
    patterns = {
        "password": "HIGH",
        "api key": "HIGH",
        "secret": "MEDIUM",
        "token": "MEDIUM",
        "private key": "CRITICAL",
        "aws access": "CRITICAL",
        "client secret": "HIGH"

    }

    found = []

    for pattern, severity in pattern.items():
        if pattern in code.lower():
            found.append({
                "type": pattern,
                "severity": severity
            })
        return found


    secrets_list = ["password", "api key", "secret", "token", "private key"]
    found = []

    for secret in secrets_list:
        #.lower() makes search case insensitive
        if secret in code.lower():
            found.append(secret)
    
    return found

# @app.route() is a DECORATOR and tells flask someone visits ('/') run this function
@app.route('/')
def home():
    return jsonify({
        "app": "Secret Scanner API",
        "version": "1.0",
        "creator": "Adesh Gore",
        "status": "Online",
        "endpoints": {
            "scan": "POST /scan",
            "health": "GET /health",
            "stats": "GET /stats"
        }
    })


# this accepts only POST requests and GET wont work here
@app.route('/scan', methods=['POST'])
def scan():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
            
        code = data.get('code', '')

        if not code:
            # return erroe and give 400 status code
            return jsonify({"error": "No code provided"}), 400
    
        # call our scanner function
        secrets = scan_for_secrets(code)

        stats["total_scans"] += 1
        stats["total_secrets_found"] += len(secrets)

        # return results as json
        return jsonify({
        "scanned": True,
        "secrets_found": len(secrets),
        "secrets": secrets,
        "safe": len(secrets) == 0,  
        "message": "✅ Code is safe!" if len(secrets) == 0 else f"⚠️ Found {len(secrets)} security issues!"
    })

    except Exception  as e:
        return jsonify({
        "error": "Internal server error",
        "message": str(e)
    }), 500


@app.route('/stats')
def get_stats():
    return jsonify({
        "total_scans": stats["total_scans"],
        "total_secrets_found": stats["total_secrets_found"],
        "average_secrets_per_scan": round(stats["total_secrets_found"] / stats["total_scans"], 2) if stats["total_scans"] > 0 else 0
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
    print("URL: http://localhost:5000")
    print("🔍 Ready to Scan for Secrets!")
    print("=" * 50)

    #debug=TRUE gives helpful error messages and never use this in production!
    app.run(debug=True, port=5000)



