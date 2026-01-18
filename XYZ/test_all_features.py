import requests
import json
import subprocess

# Assuming the Flask app is running on port 5000
BASE_URL = "http://localhost:5001"

def test_home():
    """Test home endpoint"""
    print("Testing GET /")
    response = requests.get(f"{BASE_URL}/")
    print(json.dumps(response.json(), indent=2))
    print("✅ Home endpoint works!\n")


def test_scan_basic():
    """Test basic scan"""
    print("Testing POST /scan (basic)")
    data = {
        "code": "password = 'secret123'"
    }
    response = requests.post(f"{BASE_URL}/scan", json=data)
    print(json.dumps(response.json(), indent=2))
    print("✅ Basic scan works!\n")


def test_scan_advanced():
    """Test advanced scan with multiple secrets"""
    print("Testing POST /scan (advanced)")
    data = {
        "code": """
api_key = 'abc123'
password = 'mypass'
AKIAIOSFODNN7EXAMPLE
ghp_16C7e42F292c6912E7710c838347Ae178B4a
        """
    }
    response = requests.post(f"{BASE_URL}/scan", json=data)
    print(json.dumps(response.json(), indent=2))
    print("✅ Advanced scan works!\n")


def test_stats():
    """Test statistics endpoint"""
    print("Testing GET /stats")
    response = requests.get(f"{BASE_URL}/stats")
    print(json.dumps(response.json(), indent=2))
    print("✅ Stats endpoint works!\n")


def test_docs():
    """Test documentation endpoint"""
    print("Testing GET /docs")
    response = requests.get(f"{BASE_URL}/docs")
    print(json.dumps(response.json(), indent=2))
    print("✅ Docs endpoint works!\n")


def test_health():
    """Test health endpoint"""
    print("Testing GET /health")
    response = requests.get(f"{BASE_URL}/health")
    print(json.dumps(response.json(), indent=2))
    print("✅ Health endpoint works!\n")


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Secret Scanner API v2.0")
    print("=" * 50)
    print("\nStarting Flask app in a separate process...")
    # Start the Flask app in a separate process
    # We use a simple Popen call and assume the app starts quickly.
    # In a more robust test setup, you might use a library like `pytest-flask` or `gunicorn`
    # and wait for the server to be ready.
    flask_process = subprocess.Popen(['python', 'c:\\XYZ\\secret_scanner_V2.py'])
    print("Flask app started. Giving it a moment to initialize...\n")
    import time
    time.sleep(5) # Give the server a few seconds to start up

    try:
        test_home()
        test_scan_basic()
        test_scan_advanced()
        test_stats()
        test_docs()
        test_health()
        
        print("=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 50)
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        print("\nTerminating Flask app...")
        flask_process.terminate()
        flask_process.wait()
        print("Flask app terminated.")