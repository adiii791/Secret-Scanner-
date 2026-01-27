# Flask Concepts I Now Understand

## What is Flask?
- Micro web framework for Python
- "Micro" = lightweight, minimal
- Lets us build web APIs easily
- Similar to: Express (Node.js), Sinatra (Ruby)

## Key Concepts

### 1. Routes
- URLs that API responds to
- Example: `/`, `/scan`, `/health`
- Defined with `@app.route('/path')`

### 2. HTTP Methods
- GET: Retrieve data (like /health)
- POST: Send data (like /scan)
- PUT: Update data
- DELETE: Remove data

### 3. Request
- `request.json` - gets JSON data sent to us
- `request.args` - gets URL parameters
- `request.headers` - gets HTTP headers

### 4. Response
- `jsonify()` - converts Python dict to JSON
- Status codes: 200 (OK), 400 (Bad Request), 500 (Error)

### 5. Decorator (@)
- `@app.route()` is a decorator
- Wraps function with extra functionality
- Tells Flask which function handles which URL

## What I Built
- REST API with 3 endpoints
- Accepts JSON input
- Returns JSON output
- Professional structure

