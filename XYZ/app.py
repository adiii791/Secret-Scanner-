# from flask import Flask

# app = Flask(__name__)

# @app.route('/')
# def home():
#     return "Hello! My First API is working! 🚀"

# if __name__ == '__main__':
#     app.run(debug=True)
    
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Secret Scanner API",
        "version": "1.0.0",
        "status": "Running",
        "Creator": "AG Jod"

    })

if __name__ == '__main__':
    app.run(debug=True)
