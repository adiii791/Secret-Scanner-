#  Secret Scanner API v2.0
🌐 LIVE DEMO
**API URL:** http://adiii.pythonanywhere.com/
Working Endpoints

### Home
```
GET http://adiii.pythonanywhere.com/
```

### Health Check
```
GET http://adiii.pythonanywhere.com/health

### Statistics
```
GET http://adiii.pythonanywhere.com/stats
```

### Scan Code
```bash
curl -X POST http://adiii.pythonanywhere.com/scan \
  -H "Content-Type: application/json" \
  -d '{"code":"password=123"}'

## Features
✅ Detects hardcoded passwords
✅ Finds API keys and tokens
✅ JSON responses
✅ Error handling
✅ Statistics tracking
✅ Live and accessible 24/7

## Tech Stack
- Python 3.10
- Flask 3.0
- PythonAnywhere hosting
- REST API architecture

**Status:** 🟢 Live and Running

